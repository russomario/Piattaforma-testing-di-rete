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

"""Script per estrarre dai report di gatling le seguenti metriche:
numberOfRequests, meanResponseTime, standardDeviation e throughput.
Una volta estratte le salva in un file locale.
Posizione: macchina gatling @ /home/mario-gatling/gatling_3.6.1/stats_extractor.py
"""


import json
from sys import argv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type = str, help = "Input file", required = True)
parser.add_argument("-o", "--output", type = str, help = "Output file", required = True)
parser.add_argument("--attackID", type = str, help = "ID configurazione attacco", required = True)
parser.add_argument("--serverID", type = int, help = "ID configurazione server", required = True)

args = parser.parse_args()



data = ""

with open(args.input, "r") as stats:
    data = json.load(stats)

numb_req = data["stats"]["numberOfRequests"]
numb_req["%ok"] = (numb_req["ok"] / numb_req["total"]) * 100
numb_req["%ko"] = (numb_req["ko"] / numb_req["total"]) * 100
rt_avr = data["stats"]["meanResponseTime"]
std_dev = data["stats"]["standardDeviation"]
thrput = data["stats"]["meanNumberOfRequestsPerSecond"]

clean_stats = {
        "ID_Attack": args.attackID,
        "ID_Server": args.serverID,
        "stats": {
        "numberOfRequests": numb_req,
        "meanResponseTime": rt_avr,
        "standardDeviation": std_dev,
        "throughput": thrput
    }
}

with open(args.output, "w") as clean:
    clean.write(json.dumps(clean_stats, indent = 4))