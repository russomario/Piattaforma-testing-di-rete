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

"""Script per la conversione in json compatibile con elasticsearch delle metriche di zabbix
Posizione: macchina monitor
"""

import argparse
from os import remove

args = None

def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    parser.add_argument("--convert", action="store_true")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

def get_path():
    return f"/root/zabbix_extractor/output/{args.attackID}_{args.serverID}.json"

def get_formatted(filename):
    pre = filename.split(".")[0]
    print(f"{pre}_formatted.json")
    return f"{pre}_formatted.json"

def format():
    with open(get_path()) as original:
        with open(get_formatted(get_path()), "w") as new:
            orig_data = original.read()
            new_data = orig_data[1:-1].replace("}, {", "}\n{")
            new.write(new_data)

def delete():
    path = get_formatted(get_path())
    remove(path)

main()
if args.convert:
    format()
else:
    delete()