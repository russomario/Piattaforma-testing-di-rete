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

"""Script per la conversione e il caricamento dei file di output
Posizione: macchina monitor
"""

import subprocess
import argparse

args = None

def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    args = parser.parse_args()

def start():
    # inizio la conversione del pcap
    cmd_pcap = "python3 pcap_converter.py --attackID {} --serverID {} --convert"\
                .format(args.attackID, args.serverID)
    subprocess.call(cmd_pcap, shell=True)

    # formattazione del json zabbix
    cmd_zabbix = "python3 zabbix_formatter.py --attackID {} --serverID {} --convert"\
                 .format(args.attackID, args.serverID)
    subprocess.call(cmd_zabbix, shell=True)
    
    # upload dei json
    cmd_upload = "python3 uploader.py --attackID {} --serverID {}"\
                 .format(args.attackID, args.serverID)
    subprocess.call(cmd_upload, shell=True)


def clean():
    # rimuovo il file json della conversione da pcap
    cmd_pcap = "python3 pcap_converter.py --attackID {} --serverID {} --delete"\
                .format(args.attackID, args.serverID)
    subprocess.call(cmd_pcap, shell=True)
    # rimuovo il file json della conversione da pcap
    cmd_zabbix = "python3 zabbix_formatter.py --attackID {} --serverID {} --delete"\
                .format(args.attackID, args.serverID)
    subprocess.call(cmd_zabbix, shell=True)


if __name__ == "__main__":
    main()
    start()
    clean()
