import paramiko

from datetime import datetime
from time import sleep
import requests
import json
import pandas as pd
import time
import os
import csv

import signal
import sys

from scipy import stats
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import matplotlib.pyplot as plt
import numpy as np

from analytics.init_logger import init_logger
from scp import SCPClient, SCPException
from analytics.network.publisher import MessagePublisher
from analytics.network.mqtt import MQTT
from analytics.policy_manager import PolicyManager
from analytics.models.metric import Measurement

from experiments.ssh import *
from experiments.data import *


'''
Requirements
_

* 1. Execute experiment, run commands and collect logs
* 2. Change the workload according to the experiment needs
* 3. Cleanup in general

Spec
_

* Profiling

1. Run profiler with custom output log file (adding metadata about the execution)
2. SCP output log file from the Raspberry Pi
3. Process the logs, converting the JSON format to a CSV file
4. Name the CSV file with according metadata attributes to identify it

Name suggestion: `profiler-<timestamp->-<execution-number>`.{txt, csv}
'''

EDGE_NODE_HOSTNAME = '192.168.3.11'
EDGE_NODE_SSH_USERNAME = 'pi'
EDGE_WORKDIR = '/home/pi/'

CLOUD_NODE_HOSTNAME = '192.168.3.7'
CLOUD_NODE_SSH_USERNAME = 'netoax'
CLOUD_WORKDIR = '/home/netoax/experiment'

RAW_DATA_LOGS_OUTPUT_DIR = '/Users/jneto/msc/workspace/results/staging'
LOG_FILE_NAME_FORMAT = '*.txt'

BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

# DATA_THROUGHPUT_FACTORS = ['0.001', '0.001', '0.0001', '0.00001', '0.0']
APPLICATIONS = ['ddos-10s', 'ddos-128s']
DATA_THROUGHPUT_FACTORS = [500]
STRATEGIES = ['policy']
NUMBER_OF_EVENTS_TO_PUBLISH = '100000'

# EXECUTION_MODE = os.environ.get('EXECUTION_MODE') || 'test'

mqtt_local_hostname = '192.168.3.11'
mqtt = MQTT(hostname=mqtt_local_hostname, port=1883)
publisher = MessagePublisher(mqtt)
# mqtt.start()

logger = init_logger(__name__, testing_mode=False)
policy_manager = PolicyManager('./analytics/policies.xml', logger, publisher)


'''
    Dependencies start/stop
'''

#   ***** LOG FILENAMES STANDARD
#   `node:software:execution:throughput:timestamp`
#   e.g. `edge:profiler:
# `

def _start_edge_profiler(client, execution_number):
    filename = 'edge:profiler:{}:{}.txt'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'export $(cat ./profiler.env) && ./profiler > {} 2>&1 &'.format(filename)
    stdin, stdout, stderr = client.exec_command(cmd)
    return filename

def _start_cloud_profiler(client, execution_number):
    filename = 'cloud:profiler:{}:{}.txt'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'cd experiment && export $(cat ./profiler.env) && ./profiler > {} 2>&1 &'.format(filename)
    stdin, stdout, stderr = client.exec_command(cmd)
    return filename

def _stop_profiler(client):
    kill_application(client, 'profiler')

def _start_edge_decision_engine(client, execution_number):
    filename = 'edge:decision:{}:{}.txt'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'cd {} && export $(cat ./decision.env) && ./decision > {} 2>&1 &'.format(EDGE_WORKDIR, filename)
    stdin, stdout, stderr = client.exec_command(cmd)

def _start_cloud_decision_engine(client, execution_number):
    filename = 'cloud:decision:{}:{}.txt'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'cd {} && export $(cat ./decision.env) && ./decision > {} 2>&1 &'.format(CLOUD_WORKDIR, filename)
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_decision_engine(client):
    kill_application(client, 'decision')

def _start_analytics(client):
    cmd = 'cd analytics && source ./env/bin/activate && python -m main > analytics.txt 2>&1 &'
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_analytics(client):
    kill_application(client, 'python')

def _start_iperf(client):
    cmd = 'iperf3 -s'
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_iperf(client):
    kill_application(client, 'iperf')

'''
    CEP Application data
'''

def _from_row_to_dict(row):
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
    return data

def _get_cep_job_id():
    r = requests.get('http://{}:8282/jobs'.format(EDGE_NODE_HOSTNAME))
    response = r.json()
    return response['jobs'][0]['id']

def _save_flink_overall_metrics(job_id, execution_number, application):
    r = requests.get('http://{}:8282/jobs/{}'.format(EDGE_NODE_HOSTNAME, job_id))
    response = r.text
    file = open('./results/flink-execution-{}-workload-{}-{}.json'.format(execution_number, application, datetime.now()).replace(" ", ""), "w")
    file.write(response)
    file.close()

def _publish_application_name(name):
    mqtt.start()
    publisher.publish_application_name(name)
    mqtt.stop()
    sleep(2 * 60)

'''
    Experiment Orchestration
'''

def start_dependencies(edgeClient, cloudClient, application, execution):
    _start_analytics(edgeClient)
    _start_edge_profiler(edgeClient, execution)
    _start_cloud_profiler(cloudClient, execution)
    _start_iperf(cloudClient)

    start_cep_application(edgeClient, application)
    _start_edge_decision_engine(edgeClient, execution)
    _start_cloud_decision_engine(cloudClient, execution)

    sleep(5)

def stop_and_get_logs(edgeClient, cloudClient, application, throughput, execution):
    stop_cep_application(edgeClient, application)
    _stop_decision_engine(edgeClient)
    _stop_decision_engine(cloudClient)

    output_dir = f"{RAW_DATA_LOGS_OUTPUT_DIR}/{execution}/{application}/{throughput}"
    get_logs(edgeClient, EDGE_WORKDIR, LOG_FILE_NAME_FORMAT, output_dir)
    get_logs(cloudClient, CLOUD_WORKDIR, LOG_FILE_NAME_FORMAT, output_dir)

    _stop_profiler(edgeClient)
    _stop_profiler(cloudClient)
    _stop_iperf(cloudClient)
    _stop_analytics(edgeClient)

# save to -> ../results/staging/:execution/:application/:throughput/file.txt
def run_unit_execution(edgeClient, cloudClient, application, throughput, execution):
    start_dependencies(edgeClient, cloudClient, application, execution)
    _publish_application_name(application)

    mqtt.start()
    publish_workload_data(publisher, [throughput], NUMBER_OF_EVENTS_TO_PUBLISH)
    mqtt.stop()

    print('\tExtracting logs from nodes')
    stop_and_get_logs(edgeClient, cloudClient, application, throughput, execution)
    print('Done\n')


def start_experiment(edgeClient, cloudClient):
    number_of_executions = 1
    print('Running experiment: strategies x throughputs (30x)')

    for s in STRATEGIES:
        for f in DATA_THROUGHPUT_FACTORS:
            for i in range(number_of_executions):
                print('strategy: {}, throughput: {}, execution: {}'.format(s, f, i+1))
                run_unit_execution(edgeClient, cloudClient, 'ddos-10s', f, i+1)

# --------------- graphs

edgeClient = start_ssh_connection(EDGE_NODE_HOSTNAME, EDGE_NODE_SSH_USERNAME)
cloudClient = start_ssh_connection(CLOUD_NODE_HOSTNAME, CLOUD_NODE_SSH_USERNAME)

def signal_handler(sig, frame):
    print('Exiting gracefully')
    mqtt.stop()
    _stop_profiler(edgeClient)
    _stop_profiler(cloudClient)
    kill_application(edgeClient, 'java')
    _stop_iperf(cloudClient)
    _stop_decision_engine(edgeClient)
    _stop_decision_engine(cloudClient)
    _stop_analytics(edgeClient)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
start_experiment(edgeClient, cloudClient)
cloudClient.close()

# TODO: 1. adicionar categorizacaoo das colunas e gerar CSV consolidado dos dados.
# TODO: 2. adicionar coleta de metricas gerais do CEP (DONE)
# TODO: 3. adicionar processamento de CSVs pra gerar imagens com Python mesmo
    # - grafico de linha, calculo de dis. normal, metricas como media, mediana, etc, etc
# TODO: 4. adicionar um arquivo com as execuções, intervalos de tempos e fatores envolvidos no experimento
# e.g. 0 -> profiler -> f0.001 -> between 23h and 1h

# TODO: 5. diferenciar execucoes de teste de execucoes reais: lifecycle do flink é gerenciado pelo decision engine