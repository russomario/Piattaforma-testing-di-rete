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

from datetime import datetime
import paramiko
from time import sleep, time
import argparse

accounts = {}
args = None

def main():
    global args, accounts
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    parser.add_argument("--credentials", type = str, help = "File where are store credentials", required = True)
    args = parser.parse_args()
    accounts = parse_credentials()
    
    # connect_monitor()
    connect_gatling()

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def connect_monitor():
    monitor_conn = paramiko.SSHClient()
    monitor_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        monitor_conn.connect(hostname = accounts["monitor"]["address"],
                             username = accounts["monitor"]["username"],
                             password = accounts["monitor"]["password"])
        print(f"[ {get_timestamp()} ] Connessione al monitor avvenuta con successo")
        monitor_import(monitor_conn)
        monitor_conn.close()
        print(f"[ {get_timestamp()} ] Connessione chiusa con la macchina monitor")
    except Exception as e:
        print(f"[ {get_timestamp()} ] Errore di connessione alla macchina monitor")
        exit(1)

def connect_gatling():
    gatling_conn = paramiko.SSHClient()
    gatling_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        gatling_conn.connect(hostname = accounts["gatling"]["address"],
                             username = accounts["gatling"]["username"],
                             password = accounts["gatling"]["password"])
        print(f"[ {get_timestamp()} ] Connessione alla macchina gatling avvenuta con successo")
        gatling_import(gatling_conn)
        gatling_conn.close()
        print(f"[ {get_timestamp()} ] Connessione chiusa con la macchina gatling")
    except Exception as e:
        print(f"[ {get_timestamp()} ] Errore di connessione alla macchina gatling")
        exit(1)

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

def monitor_import(monitor_conn):
    cmd = f"cd /root/analisi && python3 main.py --attackID {args.attackID} --serverID {args.serverID}"
    stdin, stdout, stderr = monitor_conn.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print(f"[ {get_timestamp()} ] Caricamento pcap e zabbix completato")
    else:
        print(f"[ {get_timestamp()} ] Caricamento pcap e zabbix fallito. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

def gatling_import(gatling_conn):
    cmd = f"cd ./gatling_3.6.1 && python3 uploader.py --attackID {args.attackID} --serverID {args.serverID} --elkip {accounts['monitor']['address']}"
    stdin, stdout, stderr = gatling_conn.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    if (exit_status == 0):
        print(f"[ {get_timestamp()} ] Caricamento gatling completato")
    else:
        print(f"[ {get_timestamp()} ] Caricamento gatling fallito. stderr: {stderr.read().decode()}. Code: {exit_status}")
        exit(1)

if __name__ == "__main__":
    main()