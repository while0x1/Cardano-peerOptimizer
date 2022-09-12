#!/usr/bin/env python3
'''
Generates a topology file
'''
import time
import json
import socket
import argparse
import random
import subprocess
import sys

def is_open(dns_or_ip, port):
    '''
    Checks to see if port is open via sockets
    '''
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.settimeout(0.6)
    try:
        soc.connect((dns_or_ip, int(port)))
        soc.shutdown(2)
        return True
    except:
        return False

def cncli(dns_or_ip, port):
    '''
    Checks to see if port is open via cncli
    Does initial Cardano handshake
    '''
    try:
        proc = subprocess.Popen(["cncli ping -h " + dns_or_ip + " -p " + str(port)],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        response = json.loads(out)
        print(response,err)
        status = response['status']
        if status == "ok":
            return True
        return False
    except Exception as err:
        print(err)
        return False

def add_static_peers(staticpeers,relays):
    '''
    List example:
    [{"addr": "relay2.weebl.me", "port": 3001, "valency": 1},
    {"addr": "relay2.stakepool.quebec", "port": 6000, "valency": 1}]
    '''
    with open(staticpeers, "r") as read_file:
        mypeers = json.load(read_file)
    return mypeers + relays

def remove_dups_stakesort(relays):
    '''
    Removes duplicate entries and keeps entry with highest stake
    '''
    newtopo = []
    duplicates = 0
    relays_sorted = sorted(sorted(relays, key = lambda x: (x['stake']),reverse=True),
         key = lambda x: (x['addr'], x['port']))
    relays_n_ports = []
    for elem in relays_sorted:
        relay_port = f"{elem['addr']}_{elem['port']}"
        print(relay_port)
        if relay_port in relays_n_ports:
            # since we sorted by stake no need
            # to add
            duplicates += 1
        else:
            relays_n_ports.append(relay_port)
            newtopo.append(elem)
    return newtopo,duplicates

def create_relay_list():
    '''
    Creates initial list of relays that are reachable
    '''
    ###SETUP PARAMS
    rttconfig = 750
    stakeconfig = 100000000000000
    stakeconfigmin = 20000000000000
    ###########
    relays = []
    badrelays = []

    print("Starting topology optimization...")
    with open("pooldetails.json","r") as file_to_read:
        pool_data = json.load(file_to_read)
    for pool in pool_data:
        stake = pool['stake']
        if int(stake) < stakeconfig and int(stake) > stakeconfigmin :
            for rel in pool['relays']:
                ip = rel["ipv4"]
                port = rel["port"]
                dns = rel['dns']
                start = time.time()
                if dns is None:
                    checkopen = is_open(ip, port)
                    if not checkopen:
                        badrelays.append({"addr": ip, "port": port})
                        print(ip, "Not Contactable")
                    else:
                        rtt = round((time.time() - start) * 1000,2)
                        if rtt < rttconfig:
                            relays.append(
                                {"addr": ip,"port": port,"valency": 1,"rtt": rtt,"stake": stake}
                                )
                else:
                    checkopen = is_open(dns, port)
                    if not checkopen:
                        badrelays.append({"addr": dns, "port": port})
                        print(dns, "Not Contactable")
                    else:
                        rtt = round((time.time() - start) * 1000, 2)
                        if rtt < rttconfig:
                            relays.append(
                                {"addr": dns,"port": port,"valency": 1,"rtt": rtt,"stake": stake}
                                )
    # write bad relays?
    return relays

def main():
    '''
    Main loop
    '''
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()

    parser.add_argument('--peersfile', '-f', type=str, required=False, help='Static peers file')
    group.add_argument('--rtt', '-t', action='store_true', required=False,
        help='Sort by round trip time')
    group.add_argument('--stake', '-s', action='store_true', required=False, help='Sort by stake')
    group.add_argument('--random', '-r', action='store_true', required=False,
        help='Want to try a randomly sorted topology')
    parser.add_argument('--cncli', '-c', action='store_true',
        help='Add cncli check, default is socket check')

    try:
        args = parser.parse_args()
    except argparse.ArgumentError:
        sys.exit(2)

    relays_list = create_relay_list()
    relays_list,dups = remove_dups_stakesort(relays_list)
    with open("filteredrelays.json","w") as file_to_write:
        json.dump(relays_list,file_to_write,indent=4)

    if args.rtt:
        sort_method = "rtt"
        relays_list = sorted(relays_list, key= lambda x: x['rtt'])
    elif args.stake:
        sort_method = "stake"
        relays_list = sorted(relays_list, key= lambda item: item['stake'], reverse=True)
    elif args.random:
        sort_method = "randomly"
        random.shuffle(relays_list)
    else:
        sort_method = "name"

    cncli_removes = 0
    if args.cncli:
        for relay in relays_list:
            print(relay)
            print(relay['addr'],relay['port'])
            cncli_ping = cncli(relay['addr'],relay['port'])
            if not cncli_ping:
                print(f"Removing {relay['addr']} listening on port {relay['port']} relay from list")
                relays_list.remove(relay)
                cncli_removes += 1

    if args.peersfile:
        relays_list = add_static_peers(args.peersfile,relays_list)

    # Make final list
    final_relay_list = {"Producers": relays_list }

    for relays in final_relay_list["Producers"]:
        print(relays)
    print(f'{len(final_relay_list["Producers"])} Peers')

    with open("topology.json","w") as file_to_write:
        json.dump(final_relay_list,file_to_write,indent=4)
    print (f"The topology file was sorted by {sort_method}")
    print(f"Number of duplicates removed is {dups}")
    if args.cncli:
        print(f"Number of cncli removes are {cncli_removes}")
    print("Process Complete..")

if __name__ == "__main__":
    main()
