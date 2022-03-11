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

"""Classe che si occupa del rollback su Proxmox tramite API.
Per tutte le richieste è necessario impostare verify pari a False in quanto
Proxmox non supporta la verifica del certificato SSL. 
Posizione: macchina controller/esterna
"""

import requests
import urllib3
from datetime import datetime

class Rollbacker:

    PROXMOX_URL = None
    GET_TOKEN = "/api2/json/access/ticket"
    ROLLBACK = "/api2/json/nodes/{node}/qemu/{vmid}/snapshot/{snap_name}/rollback"

    credentials = {}

    def __init__(self, url, username, password):
        self.PROXMOX_URL = url
        self.credentials ["username"] = username
        self.credentials["password"] = password
        self.disable_ssl_warnings()

    def disable_ssl_warnings(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_tickets(self):
        # TODO: aggiungere handling di errori
        response = requests.post(self.PROXMOX_URL + self.GET_TOKEN, data = self.credentials, verify = False)
        dic = response.json()
        return dic['data']['ticket'], dic['data']['CSRFPreventionToken']

    def rollback(self, node, vmid, snap_name):
        # TODO: aggiungere handling di errori
        ticket, csrf = self.get_tickets()
        cookies = {"PVEAuthCookie": ticket}
        headers = {"CSRFPreventionToken": csrf}
        rollback_req = requests.post(self.PROXMOX_URL + self.ROLLBACK.format(node = node, vmid = vmid, snap_name = snap_name),
                                    cookies = cookies, headers = headers, verify = False)
        if rollback_req.status_code == 200:
            print(f"[ {self.get_timestamp()} ] Rollback avvenuto con successo. Code: 200")
        else:
            print(f"[ {self.get_timestamp()} ] Rollback fallito. Code:", rollback_req.status_code)
            raise Exception("Not able to rollback. Status code {}".format(rollback_req.status_code))
    
    def get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")