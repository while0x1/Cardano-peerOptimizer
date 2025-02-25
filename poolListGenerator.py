#!/usr/bin/env python3
import json
import requests
import time
import sys

pooldetails = []
allrelays = []
filteredrelays = []

def get_relays(headers):
    try:
        s = requests.Session()
        r = s.get("https://api.koios.rest/api/v1/pool_list",headers=headers)
        relays = json.loads(r.content)
        #print(r.content)
        for n in relays:
            allrelays.append(n)
    except Exception as e:
        print("Gathering relays for headers={} there was an error: {}".format(headers, e))

def create_pool_list():
    try:
        s = requests.Session()
        r = s.get("https://api.koios.rest/api/v1/tip")
        if r.status_code == 200:
            #print(r.content)
            epoch = json.loads(r.content)
            epoch  = str(epoch[0]['epoch_no']-1)
            print("Gathering active stake for epoch {}.".format(epoch))
            #sys.exit()
    except Exception as e:
        print(e)
    try:
        headers = {"Accept": "application/json", "Range": "0-999"}
        get_relays(headers)
        headers={"Accept": "application/json","Range": "1000-1999"}
        get_relays(headers)
        headers = {"Accept": "application/json", "Range": "2000-2999"}
        get_relays(headers)
        headers = {"Accept": "application/json", "Range": "3000-3999"}
        get_relays(headers)
    except Exception as e:
        print(e)

    ar = 0
    for n in allrelays:
        #print(n)
        poolid = n['pool_id_bech32']
        data_payload = {'_pool_bech32_ids': [poolid]}
        json_payload = json.dumps(data_payload)
        #stakequery = "https://api.koios.rest/api/v0/pool_history?_pool_bech32=" + poolid + "&_epoch_no=" + epoch
        stakequery = "https://api.koios.rest/api/v1/pool_info"
        try:
            r = s.post(stakequery,data=json_payload)
            ar += 1
            print(f'Remaining Queries: {len(allrelays)-ar}')
            if r.status_code == 200:
                stake = json.loads(r.content)
                #print(stake)
                stake = stake[0]["active_stake"]
                pooldetails.append({'id': poolid,'stake': stake,'relays':n['relays']})
            #print(pooldetails)
        except Exception as e:
            print("It is likely that active stake is zero or pledge not met for {} with error: {}".format(poolid,e))
    with open("pooldetails.json","w") as fw:
        json.dump(pooldetails,fw)

if __name__ == "__main__":
    create_pool_list()
