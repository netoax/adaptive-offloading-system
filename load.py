# Targets: edge, cloud
# Workload: same
# Application: simple, complex
# Throughput: 5000 m/s
# Metrics: CPU, memory, bandwidth, latência do CEP, data from one attacker

from time import sleep
from rich import print

from data import *
from ssh import *
from flink import *

from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher
from analytics.network.subscriber import MessageSubscriber

# DATA_THROUGHPUT_FACTORS = ['0.1', '0.01', '0.001', '0.0001']
DATA_THROUGHPUT_FACTORS = ['0.0001']
NUMBER_OF_EVENTS_TO_PUBLISH = '200000'
NUMBER_OF_EXECUTIONS = 1

LOG_FILE_NAME_FORMAT = '*.nmon'
RAW_DATA_LOGS_OUTPUT_DIR = './results/nmon/'

EDGE_NODE_HOSTNAME = '192.168.3.11'
EDGE_NODE_SSH_USERNAME = 'pi'
EDGE_WORKDIR = '/home/pi/'

CEP_APPLICATION = 'ddos-128s'

SLEEP_INTERVAL_SECONDS = 120

mqtt_local_hostname = '192.168.3.11'
mqtt = MQTT(hostname=mqtt_local_hostname, port=1883)
publisher = MessagePublisher(mqtt)
subscriber = MessageSubscriber(mqtt)

client = start_ssh_connection(EDGE_NODE_HOSTNAME, EDGE_NODE_SSH_USERNAME)

received_response_events = 0

def _parse_flink_response(response):
    return {
        "recordsSent": response['vertices'][0]['metrics']['write-records']
    }

def count_received_response_data(mosq, obj, msg):
    print('receiving response: ', msg)
    received_response_events += 1

for n in range(NUMBER_OF_EXECUTIONS):
    print('CEP application loading test')
    start_nmon(client)

    sleep(SLEEP_INTERVAL_SECONDS)
    start_cep_application(client, CEP_APPLICATION)
    sleep(SLEEP_INTERVAL_SECONDS)
    n1 = get_number_of_starts_cep(client)

    mqtt.start()
    subscriber.on_cep_response(count_received_response_data)
    publish_workload_data(publisher, DATA_THROUGHPUT_FACTORS, NUMBER_OF_EVENTS_TO_PUBLISH)

    sleep(SLEEP_INTERVAL_SECONDS)
    get_logs(client, EDGE_WORKDIR, LOG_FILE_NAME_FORMAT, RAW_DATA_LOGS_OUTPUT_DIR)
    # response = save_flink_overall_metrics(EDGE_NODE_HOSTNAME, n, CEP_APPLICATION)
    # parsed_response = _parse_flink_response(response)
    n2 = get_number_of_starts_cep(client)

    stop_cep_application(client, CEP_APPLICATION)
    sleep(SLEEP_INTERVAL_SECONDS)
    kill_application(client, 'nmon')
    mqtt.stop()

    print('\rrestarts: ', n2 - n1)
    print('complex events received: ', received_response_events)
    received_response_events=0
