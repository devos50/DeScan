import json
import os
import sys
from time import sleep

import requests

if len(sys.argv) == 1:
    print("No Infura base URL provided!")
    exit(1)

BLOCKS_FILE = "blocks.json"
INFURA_URL = sys.argv[1]
BLOCK_START_INDEX = 15000000

# Get the current progress
if os.path.exists("last_block.txt"):
    with open("last_block.txt") as last_block_file:
        cur_block_ind = int(last_block_file.read()) + 1
else:
    cur_block_ind = BLOCK_START_INDEX

print("Starting to crawl at block %d" % cur_block_ind)

with open(BLOCKS_FILE, "a") as blocks_file:
    while True:
        json_data = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": [str(hex(cur_block_ind)), True], "id": 1}
        response = requests.post(INFURA_URL, json=json_data)
        if response.status_code != 200:
            print("Response code: %s" % response.status_code)
            exit(1)

        json_block = response.json()["result"]
        blocks_file.write(json.dumps(json_block) + "\n")
        print("Crawled and persisted block %d" % cur_block_ind)
        cur_block_ind += 1
        sleep(1)
