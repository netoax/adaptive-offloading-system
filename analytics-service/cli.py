import json
import sys
import os
import time
import argparse
from csv import reader
from network.mqtt import MQTT
from network.publisher import MessagePublisher
import click
import pandas as pd

# Default to publish respecting original timestamp
publish_delay_in_seconds = 5

mqtt_local_hostname = os.environ.get('MQTT_LOCAL_HOSTNAME') or 'localhost'
mqtt_remote_hostname = os.environ.get('MQTT_REMOTE_HOSTNAME') or '192.168.31.3'
mqtt_remote_port = os.environ.get('MQTT_REMOTE_PORT') or '1883'

number_published_items = os.environ.get('NUMBER_PUBLISHED_ITEMS') or '1000'
throughput = os.environ.get('THROUGHPUT') or '100'
weather_data_file = os.environ.get('WEATHER_DATA_FILE') or '../weather-ready.csv'

calculated_throughput = int(number_published_items) / int(throughput)

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
        "cpu": 70,
        "memory": 70,
        "cepLatency": 50
    }
    publisher.publish_profiling_data(json.dumps(metrics))

@main.command()
def stma():
    print('a')
    pred()
    # time.sleep(5)
    # offresp()
    # time.sleep(5)
    # sresp()
    # time.sleep(5)
    # drift()

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


@main.command()
@click.option('-f', '--factor', 'factor', default='5')
@click.option('-n', '--number', 'number', default='100000')
@click.option('-c', '--chunk', 'chunk', default='100000')
@click.option('-f', '--factor', 'factor', default='5')
def botnet(factor, number, chunk):
    reader = pd.read_csv(
        'botnet_dataset_1.csv',
        usecols=['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state'],
        dtype={'stime': float, 'proto': str, 'saddr': str, 'sport': int, 'daddr': str, 'dport': int, 'bytes': int, 'state': str},
        nrows=int(number),
        chunksize=100000
    )
    now = time.time()
    count = 0
    for df in reader:
        df = df.dropna()
        for index, row in df.iterrows():
            count = count + 1
            data = {
                "timestamp": row['stime'],
                "protocol": row['proto'],
                "sourceAddr": row['saddr'],
                "sourcePort": row['sport'],
                "destAddr": row['daddr'],
                "destPort": row['dport'],
                "bytes": row['bytes'],
                "state": row['state'],
            }
            publisher.publish_network_data(json.dumps(data))
            time.sleep(float(factor))
    elapsed = time.time() - now
    print('published {} events in {} seconds/minutes'.format(count, elapsed))
    print('throughput: {}'.format(count / elapsed))

@main.command()
@click.option('-f', '--factor', 'factor', default='5')
def traffic(factor):
    # Iterate over dataset file and publish to MQTT broker
    df = pd.read_csv('./KOAK_with_header.csv', nrows=int(number_published_items))
    count = 0
    now = time.time()
    # df = df.dropna(axis=0, subset=['AirportCode'])
    # df = df.loc[df['AirportCode'] == 'KOAK']

    for index, row in df.iterrows():
        count = count + 1
        data = {
            "kind": row['Type'],
            "severity": row['Severity'],
            "description": row['Description'],
            "start_time": row['StartTime(UTC)'],
            "end_time": row['EndTime(UTC)'],
            "location_lat": row['LocationLat'] or 0.12,
            "location_lng": row['LocationLng'] or 0.12,
            "airport_code": row['AirportCode'] or 'Abcde',
        }
        publisher.publish_traffic_data(json.dumps(data))
        time.sleep(float(factor))
    elapsed = time.time() - now
    print('published {} events in {} seconds/minutes'.format(count, elapsed))
    print('throughput: {}'.format(count / elapsed))

@main.command()
@click.option('-f', '--factor', 'factor', default='5')
def weather(factor):
    df = pd.read_csv(weather_data_file, nrows=int(number_published_items))
    i = 0
    count = 0
    now = time.time()
    df = df.dropna()
    for index, row in df.iterrows():
        count = count + 1
        data = {
            "kind": row['Type'],
            "severity": row['Severity'],
            "start_time": row['StartTime(UTC)'],
            "end_time": row['EndTime(UTC)'],
            "location_lat": row['LocationLat'] or 0.12,
            "location_lng": row['LocationLng'] or 0.12,
            "airport_code": row['AirportCode'] or 'Abcde',
        }
        # print(data)
        publisher.publish_weather_data(json.dumps(data))
        time.sleep(float(factor))

        # if count >= int(throughput):
        #     elapsed = time.time() - now
        #     time.sleep(1.-elapsed)
        #     print('published ' + throughput + ' events in 1 second')
        #     count = 0
    elapsed = time.time() - now
    print('published {} events in {} seconds/minutes'.format(count, elapsed))






# saída esperada:

# Starting benchmark - <start_datetime>
# Benchmark ended - <end_datetime>

# X events published in a throughput of seconds/minutes
# X resulting events received

# Time interval of <end_datetime> - <start_datetime>




if __name__ == "__main__":
    main()