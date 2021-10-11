import pandas as pd
import json
import time
from datetime import datetime
from time import sleep

BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

DATA_THROUGHPUT_FACTORS = ['0.001']
NUMBER_OF_EVENTS_TO_PUBLISH = '500000'
CHUNK_SIZE = 100000
DATASET_PATH = './192.168.100.149.csv'

def _from_row_to_dict(row):
    return {
        "timestamp": row['stime'],
        "protocol": row['proto'],
        "sourceAddr": row['saddr'],
        "sourcePort": row['sport'],
        "destAddr": row['daddr'],
        "destPort": row['dport'],
        "bytes": row['bytes'],
        "state": row['state'],
    }

def get_row_as_dict(row):
    return {
        "timestamp": row['stime'],
        "protocol": row['proto'],
        "sourceAddr": row['saddr'],
        "sourcePort": row['sport'],
        "destAddr": row['daddr'],
        "destPort": row['dport'],
        "bytes": row['bytes'],
        "state": row['state'],
    }

def publish_botnet_data(publisher, factor='5', number='100000', chunk='100000'):
    reader = pd.read_csv(
        DATASET_PATH,
        usecols=BOTNET_DATASET_USED_COLUMNS,
        nrows=int(number),
        chunksize=CHUNK_SIZE,
    )
    now = time.time()
    count = 0
    for df in reader:
        for index, row in df.iterrows():
            count = count + 1
            data = get_row_as_dict(row)
            publisher.publish_network_data(json.dumps(data))
            time.sleep(float(factor))
    elapsed = time.time() - now
    print('\teventsPublished: ', count)
    print('\ttime spent: ', elapsed)
    print('\tthroughput: ', (count / elapsed))

def publish_workload_data(publisher, throughputs, number_events):
    for f in throughputs:
        start = datetime.now()
        print('\nfactor: ', f)
        print('\tstart: ', start)
        publish_botnet_data(publisher, f, number_events)
        # TODO: log information to metadata file
        # idle time
        end = datetime.now()
        print('\tend: ', end)
        sleep(30)

