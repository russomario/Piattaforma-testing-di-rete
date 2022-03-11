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

"""Script per il caricamento dei file pcap e zabbix
Posizione: macchina monitor
"""

from datetime import datetime
from pytz import timezone
from elasticsearch import Elasticsearch, helpers
import json
import argparse
from hashlib import md5
import traceback

client = None
args = None
counter = 0

def main():
    global client, args
    parser = argparse.ArgumentParser()
    parser.add_argument("--attackID", type = str, help = "ID of the attack", required = True)
    parser.add_argument("--serverID", type = int, help = "ID of server configuration", required = True)
    args = parser.parse_args()
    client = Elasticsearch("localhost:9200")

def get_zabbix_filename():
    return f"/root/zabbix_extractor/output/{args.attackID}_{args.serverID}_formatted.json"

def get_pcap_filename():
    return f"/root/pcap/{args.attackID}_{args.serverID}/{args.attackID}_{args.serverID}.json"

def get_data(file_type):
    if file_type == "zabbix":
        return (l.strip() for l in open(get_zabbix_filename()))
    return (l.strip() for l in open(get_pcap_filename()))

def get_index():
    attack = args.attackID
    server = args.serverID
    return "test{}_{}".format(attack.lower(), server)

def get_timestamp(epoch, type = "seconds"):
    if type == "milliseconds":
        result = datetime.fromtimestamp(int(epoch) / 1000, timezone("Europe/Rome"))
    else:
        result = datetime.fromtimestamp(int(epoch), timezone("Europe/Rome"))
    return result

def get_docs():
    global counter
    for file_type in ["pcap", "zabbix"]:
        for doc in get_data(file_type):
            try:
                dict_doc = json.loads(doc)
                dict_doc["attackID"] = args.attackID
                dict_doc["serverID"] = args.serverID
                if file_type == "zabbix":
                    dict_doc["timestamp"] = get_timestamp(dict_doc["clock"])
                    dict_doc["type"] = "zabbix_file"
                    del dict_doc["clock"]
                    del dict_doc["ns"]
                if "layers" in dict_doc:
                    dict_doc["timestamp"] = get_timestamp(dict_doc["timestamp"], type = "milliseconds")
                    if "ip" in dict_doc["layers"] and "tcp" in dict_doc["layers"]:
                        dict_doc["hash"] = get_hash(dict_doc)
                    dict_doc["type"] = "pcap_file"
                counter += 1
                yield dict_doc
            except json.decoder.JSONDecodeError as err:
                print ("ERROR for num: -- JSONDecodeError:", err, "for doc:", doc)

def get_hash(line):
    try:
        print(line)
    except Exception as e:
        pass
    ip_src = line["layers"]["ip"]["ip_ip_src"]
    ip_dst = line["layers"]["ip"]["ip_ip_dst"]
    src_port = line["layers"]["tcp"]["tcp_tcp_srcport"]
    dst_port = line["layers"]["tcp"]["tcp_tcp_dstport"]
    tcp_stream = line["layers"]["tcp"]["tcp_tcp_stream"]
    quad = f"{ip_src}{src_port}{ip_dst}{dst_port}{tcp_stream}"
    return md5(quad.encode()).hexdigest()

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

