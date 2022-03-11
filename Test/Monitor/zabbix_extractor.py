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

"""Richiede i dati al server Zabbix e li salva nella cartella output
Posizione: macchina monitor @ /root/zabbix_extractor.py
"""

import json
import requests
import argparse

URL = "http://192.168.6.75/zabbix/api_jsonrpc.php"

itemids = {
	'36786': 'Host name of Zabbix agent running',
	'36787': 'Zabbix agent ping',
	'36788': 'Version of Zabbix agent running',
	'36789': 'Maximum number of open file descriptors',
	'36790': 'Maximum number of processes',
	'36852': 'Interface ens18: Inbound packets discarded',
	'36854': 'Interface ens18: Inbound packets with errors',
	'36856': 'Interface ens18: Bits received',
	'36853': 'Interface ens19: Inbound packets discarded',
	'36855': 'Interface ens19: Inbound packets with errors',
	'36857': 'Interface ens19: Bits received',
	'36858': 'Interface ens18: Outbound packets discarded',
	'36860': 'Interface ens18: Outbound packets with errors',
	'36862': 'Interface ens18: Bits sent',
	'36859': 'Interface ens19: Outbound packets discarded',
	'36861': 'Interface ens19: Outbound packets with errors',
	'36863': 'Interface ens19: Bits sent',
	'36791': 'Number of processes',
	'36792': 'Number of running processes',
	'36793': 'System boot time',
	'36794': 'Interrupts per second',
	'36795': 'Load average (15m avg)',
	'36796': 'Load average (1m avg)',
	'36797': 'Load average (5m avg)',
	'36798': 'Number of CPUs',
	'36799': 'Context switches per second',
	'36826': 'CPU utilization',
	'36800': 'CPU guest time',
	'36801': 'CPU guest nice time',
	'36802': 'CPU idle time',
	'36803': 'CPU interrupt time',
	'36804': 'CPU iowait time',
	'36805': 'CPU nice time',
	'36806': 'CPU softirq time',
	'36807': 'CPU steal time',
	'36808': 'CPU system time',
	'36809': 'CPU user time',
	'36810': 'System name',
	'36811': 'System local time',
	'36812': 'Operating system architecture',
	'36813': 'Operating system',
	'36814': 'Software installed',
	'36815': 'Free swap space',
	'36816': 'Free swap space in %',
	'36817': 'Total swap space',
	'36818': 'System description',
	'36819': 'System uptime',
	'36820': 'Number of logged in users',
	'36821': 'Checksum of /etc/passwd',
	'36864': 'Interface ens18: Operational status',
	'36866': 'Interface ens18: Interface type',
	'36865': 'Interface ens19: Operational status',
	'36867': 'Interface ens19: Interface type',
	'36868': '/: Free inodes in %',
	'36869': '/boot: Free inodes in %',
	'36870': '/: Space utilization',
	'36872': '/: Total space',
	'36874': '/: Used space',
	'36871': '/boot: Space utilization',
	'36873': '/boot: Total space',
	'36875': '/boot: Used space',
	'36822': 'Available memory',
	'36823': 'Available memory in %',
	'36824': 'Total memory',
	'36827': 'Memory utilization',
	'36825': 'Zabbix agent availability',
}

headers = {
    'Content-Type': 'application/json',
}

credentials = {
    "username": "Admin",
    "password": "zabbix"
}

token_request = """{{
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {{
        "user": "{username}",
        "password": "{password}"
    }},
    "id": 1,
    "auth": null
}}""".format(username = credentials["username"], password = credentials["password"])

host_metrics_request = """{{
    "jsonrpc": "2.0",
    "method": "history.get",
    "params": {{
        "output": "extend",
        "history": {history},
        "time_from": {start},
        "time_till": {end}, 
        "hostids": "{hostid}"
    }},
    "auth": "{token}",
    "id": 1
}}"""

hostids_request = """{{
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {{
        "output": ["hostids"],
        "filter": {{
            "host": [
                "{hostname}"
            ]
        }}
    }},
    "auth": "{token}",
    "id": 1
}}"""

lista = """
{
    "jsonrpc": "2.0",
    "method": "item.get",
    "params": {
        "output": "extend",
        "hostids": "10447"
    },
    "auth": "ede50bd426a6a0eb750b8d5a72cb3016",
    "id": 2
}
"""
args = None

def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type = str, help = "Name of the client on Zabbix", required = True)
    parser.add_argument("--start", type = int, help = "Timestamp of the start", required = True)
    parser.add_argument("--end", type = int, help = "Timestamp of the end", required = True)
    parser.add_argument("--output", type = str, help = "File to save retrieved Zabbix data", required = True)
    args = parser.parse_args()

def get_token():
    response = requests.post(URL, headers = headers, data = token_request)
    if response.status_code == 200:
        credentials["token"] = response.json()["result"]
    else:
        raise Exception("Error retrieving zabbix token")

def get_host_metrics():
    # C'è bisogno di fare due richeste in quanto ci sono alcuni dati di tipo
    # unsigned e altri di tipo float.
    # Zabbix non li da insieme.
    response0 = requests.post(URL, headers = headers,
                                data = host_metrics_request.format(token = credentials["token"],
                                                                        hostid = get_hostid(args.name),
                                                                        start = args.start,
                                                                        end = args.end,
                                                                        history = 0))
    response3 = requests.post(URL, headers = headers,
                                data = host_metrics_request.format(token = credentials["token"],
                                                                        hostid = get_hostid(args.name),
                                                                        start = args.start,
                                                                        end = args.end,
                                                                        history = 3))
    if response0.status_code == 200 and response3.status_code == 200:
        resp0_form = format_metrics(response0.json()["result"])
        resp3_form = format_metrics(response3.json()["result"])
        with open("./output/{}".format(args.output), "w") as f:
            f.write(resp0_form[:-2])
            f.write(", ")
            f.write(resp3_form[2:])
    else:
        raise Exception("Error getting metrics")

def get_hostid(name):
    response = requests.post(URL, headers = headers,
                                data = hostids_request.format(token = credentials["token"], hostname = name))
    if response.status_code == 200:
        result = response.json()["result"]
        if len(result) == 1:
            return result[0]["hostid"]
    raise Exception("No {} on zabbix".format(name))

def format_metrics(old):
    for item in old:
        item["name"] = itemids[item["itemid"]]
    return str(old).replace("'", "\"")


if __name__ == "__main__":
    main()
    get_token()
    get_host_metrics()