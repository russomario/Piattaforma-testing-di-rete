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

"""Si occupa di modificare il file scala in modo da cambiare indirizzo IP, UsersperSec e duration
Posizione: macchina gatling @ /home/mario-gatling/gatling_3.6.1/loadtest_modifier.py
"""


import argparse

PATH = "./user-files/simulations/normal_load.scala"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type = int, required = True)
    parser.add_argument("--time", type = int, help = "Duration of the stress test in seconds", required = True)
    parser.add_argument("--ip", type = str, required = True)
    args = parser.parse_args()
    edit(args.ip, args.users, args.time)


def edit(ip, users, duration):
    modified = ""

    with open(PATH, "r") as scalaFile:
        original = scalaFile.readlines()
        for line in original:
            if "baseUrl" in line:
                modified += "  .baseUrl(\"http://{}\")\n".format(ip)
            elif "constantUsersPerSec" in line:
                modified += "  constantUsersPerSec({}).during({}.seconds)\n".format(users, duration)
            else:
                modified += line
    
    with open(PATH, "w") as scalaFile:
        scalaFile.write(modified)

main()