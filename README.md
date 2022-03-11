# LSASDC
## _Low & Slow Attack Simulator & Data Collector_

LSASDC è un tool per la simulazione di attacchi DOS low and slow e il raccoglimento di dati in ambiente simulato.

## Testbed
![Alt text](./Testbed.png?raw=true "Title")

### Web Server
È la macchina sotto attacco.
### Gatling
È la macchina che si occupa di simulare utenti legittimi che stanno usufruendo del servizio offerto dal web server.
### Network Monitor
È la macchina che si occupa di intercettare il traffico di rete.
### Attacker
È la macchina usata dell'attaccante.
### Controller
È la macchina esterna all'ambiente simulato che si occupa di avviare test e/o analisi.

# Prerequisiti
### Server
- SSH
- Zabbix client
- Apache
- NGINX
### Gatling
- SSH
- Gatling extracted in ~/gatling_3.6.1
- Python 3.8.x
### Monitor
- SSH
- tshark
- Zabbix server
- Python 3.6.x
### Kali (Attacker)
- SSH
- Python 3.9.x
### Controller
- Python 3.8.x

# Posizionamento degli scripts sulle macchine
Categoria | Nome script | Path sulla macchina | Macchina
:-------: | :---------: | --------- | --------
Test | [main.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Controller/main.py) | Test/Controller | Controller
Test | [attack_scripts.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Controller/attack_scripts.py) | Test/Controller | Controller
Test | [rollbacker.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Controller/attack_scripts.py) | Test/Controller | Controller
Test | [zabbix_extractor.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Monitor/zabbix_extractor.py) | ~/zabbix_extractor | Monitor
Test | [gatling_conf.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Gatling/gatling_conf.py) | ~/gatling_3.6.1/ | Gatling
Test | [gatling_extractor.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Gatling/gatling_extractor.py) | ~/gatling_3.6.1/ | Gatling
Analisi | [elk_importer.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Controller/elk_importer.py) | Test/Controller | Controller
Analisi | [uploader.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Gatling/uploader.py) | ~/gatling_3.6.1/ | Gatling
Analisi | [main.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Monitor/main.py) | ~/analisi | Monitor
Analisi | [pcap_converter.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Monitor/pcap_converter.py) | ~/analisi | Monitor
Analisi | [zabbix_formatter.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Monitor/zabbix_formatter.py) | ~/analisi | Monitor
Analisi | [uploader.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Monitor/uploader.py) | ~/analisi | Monitor


# Comportamento del tool

### Test
Per svolgere i test è necessario eseguire [main.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Controller/main.py) con i parametri di interesse (descritti in una delle prossime sezioni) per il caso di test in questione. <br>
Il tool avvia 3 threads:
1. Thread che si occupa di gestire la macchina Gatling. Si connette alla macchina e lancia Gatling. Dopo che è trascorso l'intervallo di tempo impostato tramite parametro avviene l'estrazione delle metriche le quali saranno salvate su un file json.
2. Thread che si occupa di gestire la macchina di monitoring. Si connette alla macchina e avvia tshark per intercettare i pacchetti e salvarli su un file pcapng.
3. Thread che si occupa di gestire la macchina Kali. Si connette alla macchina attaccante e attende il 10% del tempo totale di durata del test prima di avviare l'attacco. Gli output dello script sono salvati in un file di testo. Dopo che il 90% dell'intervallo di tempo totale dell'attacco è trascorso il thread invia un segnale SIGTERM al processo in esecuzione in modo da terminare l'attacco.

Note:
- la connessione alle macchine avviene tramite SSH.
- i file di output e la loro collocazione è descritta nella sezione apposita: "File di output".

### Analisi

Per svolgere i test è necessario eseguire [elk_importer.py](https://github.com/VSecLab/LSASDC/blob/main/Analisi/Controller/elk_importer.py) con i parametri di interesse (descritti in una delle prossime sezioni) per il caso di test in questione. <br>
Lo script si occupa di convertire in un formato compatibile con elasticsearch i file di output, in particolare le metriche Zabbix, i pcap di rete e le statistiche di Gatling.
Una volta convertiti i file il tool si occuperà di caricare i file convertiti nel database di elasticseach e successivamente eliminarli per liberare spazio sul disco.

# Descrizione parametri per il testing: main.py
nome parametro | significato | type | required
----------- | ------------- | :-------------: | :-------------:
-h, --help | Per mostrare il messaggio di aiuto | | ❌
--node | Nome del nodo di Proxmox a cui si fa riferimento | str | ✅
--vmid | VirtualMachineID: ID del server (con cui la macchina virtuale è registrata su Proxmox) su cui fare l'attacco | int | ✅
<nobr>--snapname</nobr> | Nome dello snapshot su cui dover fare il rollback prima di ogni test | str | ✅
<nobr>--no-attack</nobr> | Disabilita l'avvio degli attacchi. Viene eseguito solo il test di carico.| | ❌
--attackID | ID dell'attacco descritto sul file excel | str | ✅
--serverID | ID della configurazione del server descritta sul file excel | int | ✅
--script | Nome del tool/script da utilizzare per l'attacco. Il nome deve essere presente nel file [attack_script.py](https://github.com/VSecLab/LSASDC/blob/main/Test/Controller/attack_scripts.py) affinché possa essere usato, con altre informazione aggiuntive descritti nel file stesso | str | ✅
-c, <nobr>--connections</nobr> | Il numero di connessioni che lo script utilizzato per l'attacco dovrà creare | int | ✅
<nobr>--sleeptime</nobr> | L'intervallo di tempo in secondi tra due richieste successive del tool d'attacco | int | ✅
--random | Abilita la randomizzazione (se supportato) di parametri da usare durante l'attacco. Ad esempio: Header, lunghezza del payload etc. Se lo specifico tool non supporta randomizzazione si vetfica un eccezione | | ❌
--usec | Parametro per indicare il numero di utenti per secondo. Parametro utilizzato da Gatling per definire il carico normale | int | ✅
-t, --duration | Intervallo di tempo in secondi nel quale Gatling dovrà mantenere il numero di utenti per secondo specificato con il parametro --usec | int | ✅
--zabname | Nome con il quale il server sotto attacco è registrato su Zabbix | str | ✅
--credentials | Nome del file nel quale sono presenti le credenziali per accedere alle varie macchine dell'ambienete simulato | str | ✅
IP | Indirizzo ip del server da attaccare | str | ✅

## Esempio avvio di un test:
```
python3 main.py --node pve --vmid 178 --snapname Apache_default_configuration --attackID A12 --serverID 1 --script slowloris-gkbrk -c 300 --sleeptime 10 --usec 200 -t 600 --zabname 'Server Apache' --credentials credenziali 192.168.12.2
```

# Descrizione parametri per il testing: elk_importer.py
nome parametro | significato | type | required
----------- | ------------- | :-------------: | :-------------:
--attackID | ID dell'attacco descritto sul file excel | str | ✅
--serverID | ID della configurazione del server descritta sul file excel | int | ✅
<nobr>--credentials</nobr> | Nome del file nel quale sono presenti le credenziali per accedere alle varie macchine dell'ambienete simulato | str | ✅

## Esempio avvio di un caricamento su elasticseach:
```
python3 main.py --attackID A12 --serverID 1 --credentials credenziali
```

## Formattazione del file per le credenziali:
Ogni riga deve avere la seguente formattazione
> nome,indirizzo,username,password

Ogni riga corrisponde alle informazioni rigurdanti una singola macchina <br>
Il nome deve essere uno tra: proxmox, kali, monitor e gatling in base alla macchina a cui si sta facendo riferimento
### Esempio di contentuto del file per le credenziali:
proxmox,indirizzoproxmox,usernameproxmox@pve,passwordproxmox <br>
kali,indirizzokali,usernamekali,passwordkali <br>
gatling,indirizzogatling,usernamegatling,passwordgatling <br>
monitor,indirizzomonitor,usernamemonitor,passwordmonitor <br>

# File di output
Nota: ogni attacco è identificato univocamente dalla tupla costituita dall'id dell'attacco (attackID) e dall'id della configurazione del server (serverID)
Nome file/directory | contenuto | Macchina
------------- | ---------- | -------
~/gatling.3_6_1/results/{attackID}_{serverID}/ | cartella nel quale sono presenti tutti gli output del tool Gatling riguardo un attacco| Gatling
~/gatling.3_6_1/results/{attackID}_{serverID}/normalload.../stats.json | File nel quale vengono riportate le metriche più importanti quali: numero di richieste andate a buon fine e non, tempo di risposta medio, deviazione standard e throughput | Gatling
~/gatling.3_6_1/results/{attackID}_{serverID}/normalload.../index.html | File dove sono presenti grafici circa l'andamento delle risposte e degli utenti attivi durante l'attacco | Gatling
~/pcap/{attackID}_{serverID}/{attackID}_{serverID}.pcapng | File contenente il traffico di rete sulla quale è stato eseguito l'attacco | Monitor 
~/zabbix_extractor/output/{attackID}_{serverID}.json | File nel quale vengono raccolte le metriche di Zabbix riguardo un attaco | Monitor 
~/attacks/output/{attackID}_{serverID} | File di testo nel quale vengono scritti gli output dei tool usati per l'attacco | Kali
