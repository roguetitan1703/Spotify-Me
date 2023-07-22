import json,os
from pprint import pprint

def dump_file(file, dump_this):
    # Dump to json
    with open(file, "w") as outfile:
        json.dump(dump_this, outfile,indent=4)

def read_file(file):
    # Read from json
    if os.path.getsize(file) == 0:
        return {}
    
    else:
        with open(file) as data_file:
            data = json.load(data_file)
        return data
