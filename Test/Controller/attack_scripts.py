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

"""File dove inserire le informazioni circa gli script usati per gli attacchi.
Ogni script è inserito come dizionario con i seguenti campi:
name: è il nome con cui dovrà essere chiamato tramite il parametro --script in "tester.py"
command: il comando da terminale per avviare lo script
command_random: il comando da terminale per avviare lo script in modalità random se supportata
random: valore boolean per controllare se lo scripr support una modalità random
venv: valore boolean per controllare se è necessario attivare un ambiente virtuale prima di avviare lo script
path: percorso dove trovare lo script
autokill: valore boolean per controllare se lo script supporta la terminazione dopo un certo intervallo
di tempo in secondi
Nota: all'interno del campo command e command_random devono essere sempre presenti {conn}, {sleeptime}, {url}
e solamente nel caso autokill = True c'è da aggiungere anche {duration}
Posizione: macchina controller/esterna
"""

scripts_dict = [
    {
        "name": "slowloris-gkbrk",
        "command": "slowloris -s {conn} --sleeptime {sleeptime} -v {url}",
        "command_random": "slowloris -s {conn} --sleeptime {sleeptime} -v -ua {url}",
        "random": True,
        "venv": True,
        "path": "/home/mario-attacker/attacks/slowloris-gkbrk",
        "autokill": False
    },
    {
        "name": "slowloris-slowhttptest",
        "command": "slowhttptest -H -c {conn} -i {sleeptime} -l {duration} -v 3 -u http://{url}",
        "random": False,
        "venv": False,
        "path": "/home/mario-attacker/attacks/slowhttptest",
        "autokill": True
    },
    {
        "name": "goloris-marant",
        "command": "./main -connections={conn} -interval={sleeptime}s {url}",
        "random": False,
        "venv": False,
        "path": "/home/mario-attacker/attacks/goloris-marant",
        "autokill": False
    },
    {
        "name": "rudy-sergidelta",
        "command": "python3 rudy.py -s {conn} -t {sleeptime} {url}",
        "random": False,
        "venv": False,
        "path": "/home/mario-attacker/attacks/rudy-SergiDelta",
        "autokill": False
    }
]

def get_name_list():
    name_list = ""
    for attack in scripts_dict:
        name_list += attack["name"]
        name_list += ", "
    return name_list[:-2]
    