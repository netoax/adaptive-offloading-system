import pandas as pd
import json
import time
from datetime import datetime
from time import sleep

from experiments.flink import *

BOTNET_DATASET_USED_COLUMNS = ['pkSeqID', 'stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'pkSeqID': int, 'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

CHUNK_SIZE = 100000
DATASET_PATH = './dataset.csv'

received_response_events = [0]
lastResponseTimeAck = [time.time()]

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
        "pkSeqID": row['pkSeqID'],
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

    responseTimer = time.time()

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
                responseTimer = verify_response_time(publisher, responseTimer, data)
    elapsed = time.time() - start
    print('\teventsPublished: ', count)
    print('\ttime spent: ', elapsed)
    print('\tthroughput: ', (count / elapsed))

def verify_response_time(publisher, responseTimer, data):
    elapsed = time.time() - responseTimer
    if elapsed > 1.0:
        # print('sending response time verification')
        data['pkSeqID'] = 0
        # print(data)
        publisher.publish_network_data(json.dumps(data))
        return time.time()
    return responseTimer

def publish_workload_data(publisher, subscriber, throughputs, address, duration=30):
    last_increment_factor = 0
    start_response_count(subscriber, lastResponseTimeAck, received_response_events)

    for f in throughputs:
        number_of_events = duration * 60 * f # time in minutes x 60 seconds * throughput
        start = datetime.now()
        # amostragem = (2 * number_of_events) / 100
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

def start_response_count(subscriber, lastResponseTimeAck, counter=[0]):
    def count_received_response_data(mosq, obj, msg):
        data = json.loads(msg.payload)
        if data['pkSeqID'] == 0:
            timestamp = time.time()
            response_time = timestamp - lastResponseTimeAck[0]
            now = datetime.now()
            print({"response_time": response_time, "timestamp": now.strftime("%d/%m/%Y %H:%M:%S")})
            lastResponseTimeAck[0] = timestamp
        counter[0] += 1

    subscriber.on_cep_response(count_received_response_data)
