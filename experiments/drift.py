import pandas as pd
import json
from time import sleep

from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher
from analytics.drift.detector import Detector
from analytics.init_logger import init_logger
from datetime import datetime

DATASET_1 = '~/drive/experimentos/online-learning/csv-files/profiler-edge-ddos-10s-250.csv'
DATASET_2 = '~/drive/experimentos/online-learning/csv-files/profiler-edge-ddos-128s-750.csv'

def get_row_as_dict(row):
    return {
        "cpu": row['cpu'],
        "memory": row['memory'],
        "rtt": row['rtt'],
        "bandwidth": row['bandwidth'],
        "cepLatency": row['cepLatency']
    }

def verify_drift_occurrences(filename):
    mqtt = MQTT(hostname="192.168.3.37", port=1883)
    mqtt.start()
    publisher = MessagePublisher(mqtt)
    drift_detector = Detector("ADWIN", None, publisher, init_logger("detector", testing_mode=False))

    df = pd.read_csv(filename)
    for index, row in df.iterrows():
        # drift_detector.fit({ "result": True })
        publisher.publish_profiling_data(json.dumps(get_row_as_dict(row)))
        # sleep(0.1)

print('starting dataset A: ', datetime.now())
verify_drift_occurrences(DATASET_1)

sleep(30)
print('waiting...\n')

print('starting dataset B: ', datetime.now())
verify_drift_occurrences(DATASET_2)

# calcular throughput dos datasets