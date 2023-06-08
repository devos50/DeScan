"""
Analyze the blocks file.
"""
import json

BLOCKS_FILE = "blocks.json"
txs = 0
num_blocks = 0

with open(BLOCKS_FILE) as blocks_file:
    print("Analyzing blocks file...")
    for line in blocks_file.readlines():
        if num_blocks > 0 and num_blocks % 1000 == 0:
            print("Analyzed %d blocks..." % num_blocks)

        block_json = json.loads(line)
        num_blocks += 1
        txs += len(block_json["transactions"])

print("Blocks: %d" % num_blocks)
print("Transactions: %d" % txs)