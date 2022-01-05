import json
import sys
import os
import time
import argparse
from csv import reader
from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher
import click
import pandas as pd
from datetime import datetime
from datetime import timedelta
import csv
import numpy as np

from skmultiflow.data import SEAGenerator
from skmultiflow.trees import HoeffdingTreeClassifier
from skmultiflow.bayes import NaiveBayes
from skmultiflow.evaluation import EvaluatePrequential
from skmultiflow.data import DataStream

from experiments.data import *

# Default to publish respecting original timestamp
publish_delay_in_seconds = 5

mqtt_local_hostname = os.environ.get('MQTT_LOCAL_HOSTNAME') or 'localhost'
mqtt_remote_hostname = os.environ.get('MQTT_REMOTE_HOSTNAME') or '192.168.31.3'
mqtt_remote_port = os.environ.get('MQTT_REMOTE_PORT') or '1883'

number_published_items = os.environ.get('NUMBER_PUBLISHED_ITEMS') or '1000'
weather_data_file = os.environ.get('WEATHER_DATA_FILE') or '../weather-ready.csv'

# Initialize MQTT
mqtt = MQTT(hostname=mqtt_local_hostname)
remote_mqtt = MQTT(hostname=mqtt_remote_hostname, port=int(mqtt_remote_port))
publisher = MessagePublisher(mqtt)
remote_publisher = MessagePublisher(remote_mqtt)

mqtt.start()
# remote_mqtt.start()

@click.group()
def main():
    """
    Simple CLI
    """
    pass

@main.command()
def prof():
    metrics = {
        "bandwidth": 12.4,
        "rtt": 8.4,
        "cpu": 50,
        "memory": 70,
        "cepLatency": 50
    }
    publisher.publish_profiling_data(json.dumps(metrics))

@main.command()
def stma():
    pred()

@main.command()
@click.option('-s', '--status', 'status', default='True')
@click.option('-a', '--accuracy', 'accuracy', default='95.0')
@click.option('-p', '--precision', 'precision', default='95.0')
@click.option('-r', '--recall', 'recall', default='95.0')
def pred(status, accuracy, precision, recall):
    print(status)
    # df = df.dropna()
    prediction = {
        "status": status == 'True',
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall)
    }
    publisher.publish_offloading_prediction(json.dumps(prediction))

@main.command()
def offresp():
    print(mqtt_remote_hostname)
    remote_publisher.publish_offloading_response(json.dumps({}))

@main.command()
def sresp():
    remote_publisher.publish_state_response(json.dumps({}))

@main.command()
def stop():
    remote_publisher.publish_stop_response(json.dumps({}))

@main.command()
def drift():
    publisher.publish_detected_drift()

def clear_df(df):
    df = df.dropna()
    df = df.dropna(subset=['sport', 'dport'])
    df = df[df['sport'] != '0x0303']
    df = df[df['sport'] != '0x0303']
    df = df[df['dport'] != '0x5000']
    df = df[df['dport'] != '0xe292']
    df = df[df['proto'] != 'icmp']
    return df

@main.command()
@click.option('-n', '--number', 'number', default='100000')
@click.option('-c', '--chunk', 'chunk', default='100000')
@click.option('-t', '--throughput', 'throughput', default='500')
def botnet(throughput='500', number='100000', chunk='100000'):
    publish_botnet_data(publisher, int(throughput), number, chunk)

@main.command()
def cleanup():
    reader = pd.read_csv(
        'botnet_dataset_1.csv',
        usecols=['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state'],
        dtype={'stime': float, 'proto': str, 'saddr': str, 'sport': int, 'daddr': str, 'dport': int, 'bytes': int, 'state': str},
        nrows=int(number),
        chunksize=100000
    )
    for df in reader:
        df = df.dropna()
        for index, row in df.iterrows():
            print(row)

@main.command()
@click.option('-n', '--number', 'number', default='100000')
def generate(number):
    df = pd.read_csv('../results/profiler/profiler-execution-0-workload-ddos-10s.jar-2021-07-3121:36:44.591528.csv')
    bandwidth_std = df['bandwidth'].std()
    bandwidth_mean = df['bandwidth'].mean()
    cpu_std = df['cpu'].std()
    cpu_mean = df['cpu'].mean()
    cep_latency_std = df['cepLatency'].std()
    cep_latency_mean = df['cepLatency'].mean()
    memory_std = df['memory'].std()
    memory_mean = df['memory'].mean()
    rtt_std = df['rtt'].std()
    rtt_mean = df['rtt'].mean()

    bandwidth = np.random.normal(loc=bandwidth_mean, scale=bandwidth_std, size=int(number))
    cpu = np.random.normal(loc=cpu_mean, scale=cpu_std, size=int(number))
    cep_latency = np.random.normal(loc=cep_latency_mean, scale=cep_latency_std, size=int(number))
    memory = np.random.normal(loc=memory_mean, scale=memory_std, size=int(number))
    rtt = np.random.normal(loc=rtt_mean, scale=rtt_std, size=int(number))

    result = []

    dt = datetime(2021, 7, 1)
    end = datetime(2021, 7, 31, 23, 59, 59)
    step = timedelta(seconds=20)

    while dt < end:
        result.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
        dt += step


    header = ['bandwidth', 'cepLatency', 'cpu', 'memory', 'rtt', 'timestamp']
    with open('random_data_test.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # print(type(bandwidth))

        for i in range(bandwidth.shape[0]):
            instance = [ bandwidth[i], cep_latency[i], cpu[i], memory[i], rtt[i], result[i]]
            # print(instance)
            writer.writerow(instance)

@main.command()
def evaluate():
    df = dataset = pd.read_csv('../random_data_labeled.csv')
    df['violated'] = df['violated'].astype(np.int64)
    df = df.drop(columns=['timestamp'])
    stream = DataStream(df)
    ht = HoeffdingTreeClassifier()
    nb = NaiveBayes()
    evaluator = EvaluatePrequential(max_samples=100000,
                                max_time=1000,
                                show_plot=True,
                                metrics=['accuracy', 'kappa'])

    evaluator.evaluate(stream=stream, model=[ht, nb], model_names=['HT', 'NB'])

if __name__ == "__main__":
    main()