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

"""Script per la conversione dei file pcap in json.
Se specificato provvede anche all'eliminazione del file convertito generato.
Posizione: macchina monitor
"""

import subprocess
from os import remove
import argparse

args = None

def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    parser.add_argument("--convert", action="store_true", help = "To convert the pcap file")
    parser.add_argument("--delete", action="store_true", help = "To delete the json file (the converted pcap file)")
    args = parser.parse_args()
    
    if args.convert ^ args.delete:
        if args.convert:
            convert()
        else:
            delete()
    else:
        print("Solo un modalità per volta (convert o delete)")

def get_path():
    return f"/root/pcap/{args.attackID}_{args.serverID}/{args.attackID}_{args.serverID}.pcapng"

def get_new_path():
    pcap = get_path()
    prefix = pcap.split(".")[0]
    return f"{prefix}.json"

def convert():
    print("Starting conversion...")
    cmd = "tshark -r {} -T ek > {}".format(get_path(), get_new_path())
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = proc.stdout.read()
    print("Conversion finished")
    print(output.decode())

def delete():
    path = get_new_path()
    remove(path)

if __name__ == "__main__":
    main()