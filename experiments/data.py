import pandas as pd
import json
import time
from datetime import datetime
from time import sleep

from experiments.flink import *

BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

CHUNK_SIZE = 100000
DATASET_PATH = './dataset.csv'

received_response_events = [0]

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

def publish_botnet_data(publisher, throughput=500, number='1000000', chunk='100000'):
    reader = pd.read_csv(
        DATASET_PATH,
        usecols=BOTNET_DATASET_USED_COLUMNS,
        nrows=int(number),
        chunksize=CHUNK_SIZE,
    )
    start = time.time()
    t = time.time()

    count = 0
    events = 0

    wait = 1.0 / throughput
    tick = wait / 50.0

    for df in reader:
        row_iterator = df.iterrows()
        for index, row in df.iterrows():
                t+=wait
                time.sleep(max(0,t-time.time()))
                data = get_row_as_dict(row)
                publisher.publish_network_data(json.dumps(data))
                count += 1
    elapsed = time.time() - start
    print('\teventsPublished: ', count)
    print('\ttime spent: ', elapsed)
    print('\tthroughput: ', (count / elapsed))

def publish_workload_data(publisher, subscriber, throughputs, address, time=30):
    last_increment_factor = 0
    start_response_count(subscriber, received_response_events)

    for f in throughputs:
        number_of_events = time * 60 * f # time in minutes x 60 seconds * throughput
        start = datetime.now()
        print('\nfactor: ', f)
        print('\tstart: ', start)
        publish_botnet_data(publisher, f, number_of_events)
        end = datetime.now()
        print('\tend: ', end)
        sleep(120)
        print('\tresponses: ', received_response_events[0])
        received_response_events[0]=0
        # latency = get_mean_latency_from_job(address)
        # print('\tmean latency: ', latency)

def start_response_count(subscriber, counter=[0]):
    def count_received_response_data(mosq, obj, msg):
        counter[0] += 1

    subscriber.on_cep_response(count_received_response_data)
