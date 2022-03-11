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

"""Script per la conversione e il caricamento delle metriche di gatling
Posizione: macchina Gatling
"""

from datetime import datetime
from pytz import timezone
from elasticsearch import Elasticsearch, helpers
import json
import argparse
import traceback
import os

client = None
args = None
counter = 0

def main():
    global client, args
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    parser.add_argument("--elkip", type = str, help = "IP of the elk server", required = True)
    args = parser.parse_args()
    client = Elasticsearch(f"{args.elkip}:9200")

def get_filename():

    base = "{}/gatling_3.6.1/results/D11_1".format(os.path.expanduser("~"))
    return "{}/{}/stats.json".format(base, os.listdir(base)[0])

def get_data():
    content = ""
    with open(get_filename()) as fr:
        content = fr.read()
    content = content.replace("\n", "").replace(" ", "")
    return content

def get_index():
    attack = args.attackID
    server = args.serverID
    return "test{}_{}".format(attack.lower(), server)

def get_timestamp():
    return datetime.fromtimestamp(int(get_epoch()), timezone("Europe/Rome"))

def get_epoch():
    try:
        epoch = os.stat(get_filename()).st_mtime
        return epoch
    except Exception as e: # File not found
        print(e)
        exit(1)

def get_docs():
    global counter
    for doc in get_data().split("\n"):
        try:
            dict_doc = json.loads(doc)
            dict_doc["attackID"] = args.attackID
            dict_doc["serverID"] = args.serverID
            dict_doc["type"] = "gatling_file"
            dict_doc["timestamp"] = get_timestamp()
            del dict_doc["ID_Attack"]
            del dict_doc["ID_Server"]
            yield dict_doc
        except json.decoder.JSONDecodeError as err:
            print("ERROR for num: -- JSONDecodeError:", err, "for doc:", doc)

def upload():
    try:
        print("Attempting to index the list of docs using helpers.bulk()")

        resp = helpers.bulk(
            client,
            get_docs(),
            index = get_index()
        )
        print("helpers.bulk() RESPONSE:", resp)
        print("helpers.bulk() RESPONSE:", json.dumps(resp, indent=4))
    except Exception as err:
        traceback.print_exc()
        print("Elasticsearch helpers.bulk() ERROR:", err)
        print("count", counter)
        quit()

if __name__ == "__main__":
    main()
    upload()
