# Copyright 2021 VSecLab
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# 
# Authors:  Mario Russo gm.mario.russo@gmail.com, Massimiliano Rak Massimiliano.RAK@unicampania.it, Giovanni Salzillo giovanni.salzillo@unicampania.it
# 
# LSASDC - Low and Slow Attack Simulator and Data Collector
# https://github.com/VSecLab/LSASDC

"""Script per l'esecuzione automatica e raccolta dati per attacchi low and slow.
Posizione: macchina controller/esterna
"""


import paramiko
from time import sleep, time
import argparse
from sys import exit, argv
from rollbacker import Rollbacker
import threading
import attack_scripts as scripts
from datetime import datetime

gatling_lock = threading.Semaphore(0)
accounts = {}
args = None

def main():
    global args, accounts
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", type = str, help = "Node of Proxmox", required = True)
    parser.add_argument("--vmid", type = int, help = "Virtual Machine ID on the node (Proxmox)", required = True)
    parser.add_argument("--snapname", type = str, help = "Name of the snapshot", required = True)
    parser.add_argument("--no-attack", action = "store_true", help = "No attack should be initiated")
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    parser.add_argument("--script", type = str, help = scripts.get_name_list(), required = True)
    parser.add_argument("-c", "--connections", type = int, help = "Number of the connections to be used in the attack", required = True)
    parser.add_argument("--sleeptime", type = int, help = "Time to wait between two requests in seconds", required = True)
    parser.add_argument("--random", action = "store_true", help = "Whether the script allows you to send parameters random as options")
    parser.add_argument("--usec", type = int, help = "User per seconds to be used in Gatling", required = True)
    parser.add_argument("-t", "--duration", type = int, help = "Duration of the test in seconds", required = True)
    parser.add_argument("--zabname", type = str, help = "Name of the server on zabbix", required = True)
    parser.add_argument("--credentials", type = str, help = "File where are store credentials", required = True)
    parser.add_argument("IP", type = str, help = "IP to attack")
    args = parser.parse_args()

    accounts = parse_credentials()

    proxmox  = Rollbacker(accounts["proxmox"]["address"],
                          accounts["proxmox"]["username"],
                          accounts["proxmox"]["password"]) 
    proxmox.rollback(args.node, args.vmid, args.snapname)
   
    monitor_thread = threading.Thread(target = connect_monitor)
    kali_thread = threading.Thread(target = connect_kali)
   
    monitor_thread.start()
    if not args.no_attack:
        kali_thread.start()
    connect_gatling()

def parse_credentials() -> dict:
    """A partire dal file passato tramite --credentials fa del parsing in modo da restituire un dizionario.
    Struttura del dizionario:
    {
        {"nome1": {"address": "", "username": "", "password": ""},
        {"nome2": {"address": "", "username": "", "password": ""},
        ...
    }
    """
    try:
        with open(args.credentials, "r") as f:
            accounts = {}
            for line in f:
                if not line.startswith("#"): # ignoro i commenti
                    account_detail = {}
                    fields = line.strip("\n").split(",")
                    account_detail["address"] = fields[1]
                    account_detail["username"] = fields[2]
                    account_detail["password"] = fields[3]
                    accounts[fields[0]] = account_detail
        return accounts
    except FileNotFoundError:
        print("File non presente")
        exit(1)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_zabbix_data(monitor_conn, start: float, end: float):
    """Invia il comando alla macchina monitor di raccogliere i dati nell'intervallo
    di tempo passatogli come parametro
    """
    # viene fatto il cast in interi in quanto Zabbix accetta come
    # istanti di inizio e di fine solamente interi
    start_form = int(start)
    end_form = int(end)
    print(f"[ {get_timestamp()} ] Estrazione metriche da Zabbix iniziata")
    stdin, stdout, stderr = monitor_conn.exec_command("cd /root/zabbix_extractor && python3 zabbix_extractor.py --name '{}' --start {} --end {} --output {}"\
                                                      .format(args.zabname, start_form, end_form, "{}_{}.json".format(args.attackID, args.serverID)))
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print(f"[ {get_timestamp()} ] Estrazione metriche da Zabbix terminata")
    else:
        print(f"[ {get_timestamp()} ] Estrazione metriche da Zabbix fallita. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

def connect_gatling():
    gatling_conn = paramiko.SSHClient()
    gatling_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        gatling_conn.connect(hostname = accounts["gatling"]["address"],
                             username = accounts["gatling"]["username"],
                             password = accounts["gatling"]["password"])
        print(f"[ {get_timestamp()} ] Connessione alla macchina gatling avvenuta con successo")
        start_load(gatling_conn)
        gatling_conn.close()
        print(f"[ {get_timestamp()} ] Connessione chiusa con la macchina gatling")
    except Exception as e:
        print(f"[ {get_timestamp()} ] Errore di connessione alla macchina gatling")
        exit(1)

def start_load(gatling_conn):
    """Modifica parametri del carico. Avvio di gatling. Estrazione e pulizia statistiche.

    Modifica i parametri da usare nel test quali "UserperSec" e "duration" inviando il valore
    di questi ultimi allo script "gatling_conf.py".
    Avvia gatling e attende la terminazione del test. Terminato il test si occupa di
    estrarre solo i parametri di interesse tramite lo script "gatling_extractor.py" e di
    salvarli in locale (macchina gatling)
    """
    stdin, stdout, stderr = gatling_conn.exec_command("cd ./gatling_3.6.1 && python3 ./gatling_conf.py --users {} --time {} --ip {}"\
                                                      .format(args.usec, args.duration, args.IP))
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print(f"[ {get_timestamp()} ] Parametri del test gatling modificati")
    else:
        print(f"[ {get_timestamp()} ] Parametri del test gatling non modificati. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

    print(f"[ {get_timestamp()} ] Avvio di gatling")
    stdin, stdout, stderr = gatling_conn.exec_command("cd ./gatling_3.6.1 && ./bin/gatling.sh -rf ./results/{}_{} -s NormalLoad"\
                                                       .format(args.attackID, args.serverID))
    exit_status = stdout.channel.recv_exit_status()
    print(f"[ {get_timestamp()} ] Gatling terminato. Code: {exit_status}")
    gatling_lock.release()
    if (exit_status == 0):
        part_path = stdout.readlines()[-1]
        path_stats = "{}js/stats.json".format(part_path[32:-11])
        print(f"[ {get_timestamp()} ] Report gatling: {part_path[32:-1]}")
        print(f"[ {get_timestamp()} ] Avvio estrazione delle statistiche dal report")
        stdin, stdout, stderr = gatling_conn.exec_command("cd ./gatling_3.6.1 && python3 gatling_extractor.py -i {} -o {} --attackID {} --serverID {}"\
                                                          .format(path_stats, "{}stats.json".format(part_path[32:-11]), args.attackID, args.serverID))
        exit_status = stdout.channel.recv_exit_status()
        if (exit_status == 0):
            print(f"[ {get_timestamp()} ] Estrazione delle statistiche dal report terminata. File esportato: {part_path[32:-11]}stats.json")
        else:
            print(f"[ {get_timestamp()} ] Estrazione delle statistiche fallita. stderr: {stderr.read().decode()}. Code: {exit_status}")
            exit(1)
    else:
        print(stderr.read().decode(), exit_status, end = "")
        gatling_conn.close()
        exit(1)

def connect_monitor():
    start = time()
    monitor_conn = paramiko.SSHClient()
    monitor_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        monitor_conn.connect(hostname = accounts["monitor"]["address"],
                             username = accounts["monitor"]["username"],
                             password = accounts["monitor"]["password"])
        print(f"[ {get_timestamp()} ] Connessione al monitor avvenuta con successo")
        start_tshark(monitor_conn)
        end = time()
        get_zabbix_data(monitor_conn, start, end)
        # generate_flow(monitor_conn)
        monitor_conn.close()
        print(f"[ {get_timestamp()} ] Connessione chiusa con la macchina monitor")
    except Exception as e:
        print(f"[ {get_timestamp()} ] Errore di connessione alla macchina monitor")
        exit(1)

def start_tshark(monitor_conn):
    monitor_conn.exec_command(f"mkdir ./pcap/{args.attackID}_{args.serverID}")
    print(f"[ {get_timestamp()} ] tshark avviato")
    stdin, stdout, stderr = monitor_conn.exec_command("echo $$ ; exec tshark -i eth1 -w ./pcap/{}_{}/{}_{}.pcapng"\
                                                      .format(args.attackID, args.serverID,
                                                              args.attackID, args.serverID))
    pid = stdout.readline()
    gatling_lock.acquire() # attendo che gatling finisca
    monitor_conn.exec_command(f"kill -s SIGTERM {pid}")
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print("[ {} ] tshark terminato. Pcap generato: /root/pcap/{}_{}/{}_{}.pcapng"\
              .format(get_timestamp(), args.attackID, args.serverID, args.attackID, args.serverID))
    else:
        print(f"[ {get_timestamp()} ] tshark fallito. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

def generate_flow(monitor_conn):
    print(f"[ {get_timestamp()} ] Creazione dei flow del file {args.attackID}_{args.serverID}.pcapng")
    stdin, stdout, stderr = monitor_conn.exec_command("argus -r ./pcap/{}_{}/{}_{}.pcapng -w ./pcap/{}_{}/{}_{}.flow"\
                                                      .format(args.attackID, args.serverID,
                                                              args.attackID, args.serverID,
                                                              args.attackID, args.serverID,
                                                              args.attackID, args.serverID))
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print("[ {} ] Flow generato: /root/pcap/{}_{}/{}_{}.flow"\
              .format(get_timestamp(), args.attackID, args.serverID, args.attackID, args.serverID))
    else:
        print(f"[ {get_timestamp()} ] Flow fallito. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

def connect_kali():
    kali_conn = paramiko.SSHClient()
    kali_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        kali_conn.connect(hostname = accounts["kali"]["address"],
                          username = accounts["kali"]["username"],
                          password = accounts["kali"]["password"])
        print(f"[ {get_timestamp()} ] Connessione alla macchina kali avvenuta con successo")
        start_attack(kali_conn)
        kali_conn.close()
        print(f"[ {get_timestamp()} ] Connessione chiusa con la macchina kali")
    except Exception as e:
        print(f"[ {get_timestamp()} ] Errore di connessione alla macchina kali:", e)
        exit(1)

def start_attack(kali_conn):
    """Avvia lo script usato come tool di attacco passato come parametro --script.
    Avvia lo script dopo il 10% del tempo del test complessivo.
    Termina lo script dopo il 90% del tempo del test complessivo.
    Si occupa di gestire l'attivazione di un ambiente virtuale se necessario (si capisce dal campo venv).
    Si occupa di usare un parametro random se lo script lo support e se specificato dal parametro --random
    """
    script = get_script()
    if script:
        output = f"../output/{args.attackID}_{args.serverID}"
        cmd = "cd path && exec cmd &> output".replace("path", script['path']).replace("output", output)

        if args.random:
            if script['random']:
                cmd = cmd.repalce("cmd", script['command_random'])
            else:
                raise Exception("Script does not have the ability to run random data")
        else:
            cmd = cmd.replace("cmd", script['command'])
        
        if script['autokill']:
            cmd = cmd.replace(" exec", "").replace("{duration}", str(int(0.8 * args.duration)))
        else:
            cmd = cmd.replace("exec", "echo $$ ; exec")
        
        cmd = cmd.format(conn = args.connections, sleeptime = args.sleeptime, url = args.IP)

        if script["venv"]: # devo inserire dopo il cd nella cartella l'attivazione dell'env
            cmd = "{}&& source ./bin/activate &&{}".format(cmd.split("&&")[0], cmd.split("&&")[1])
        
        sleep(0.1 * args.duration)
        print(f"[ {get_timestamp()} ] {args.script} avviato")
        stdin, stdout, stderr = kali_conn.exec_command(cmd)
        if script['autokill']:
            exit_status = stdout.channel.recv_exit_status()
        else:
            pid = stdout.readline()
            sleep(0.8 * args.duration)
            kali_conn.exec_command("kill -s SIGKILL {}".format(pid))
        print(f"[ {get_timestamp()} ] {args.script} terminato")
    else:
        raise Exception("Script non presente")

def get_script() -> dict:
    """Ricerca dal file "scripts.py" il nome specificato tramite --script.
    Se la ricerca ha successo restituisce il dizionario con le informazioni
    circa lo script.
    """
    for script in scripts.scripts_dict:
        if args.script == script["name"]:
            return script
    return False

if __name__ == "__main__":
    main()