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

from ssh import *
from data import *


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

RAW_DATA_LOGS_OUTPUT_DIR = './results/staging'
LOG_FILE_NAME_FORMAT = '*.txt'

APPLICATIONS = ['ddos-10s']

BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

# DATA_THROUGHPUT_FACTORS = ['0.001', '0.001', '0.0001', '0.00001', '0.0']
DATA_THROUGHPUT_FACTORS = ['0.01', '0.001', '0.0001', '0.0']
NUMBER_OF_EVENTS_TO_PUBLISH = '500000'

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

def _start_edge_profiler(client, execution_number):
    filename = 'edge: profiler-execution-{}-workload-{}'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'export $(cat ./profiler.env) && ./profiler > {}.txt 2>&1 &'.format(filename)
    stdin, stdout, stderr = client.exec_command(cmd)
    return filename

def _start_cloud_profiler(client, execution_number):
    filename = 'cloud: profiler-execution-{}-workload-{}'.format(execution_number, datetime.now()).replace(" ", "")
    cmd = 'cd experiment && export $(cat ./profiler.env) && ./profiler > {}.txt 2>&1 &'.format(filename)
    stdin, stdout, stderr = client.exec_command(cmd)
    return filename

def _stop_profiler(client):
    kill_application(client, 'profiler')

def _start_edge_decision_engine(client):
    filename = 'edge: decision-logs-{}'.format(datetime.now()).replace(" ", "")
    cmd = 'cd {} && export $(cat ./decision.env) && ./decision > {} 2>&1 &'.format(EDGE_WORKDIR, filename)
    stdin, stdout, stderr = client.exec_command(cmd)

def _start_cloud_decision_engine(client):
    filename = 'cloud: decision-logs-{}'.format(datetime.now()).replace(" ", "")
    cmd = 'cd {} && export $(cat ./decision.env) && ./decision > {} 2>&1 &'.format(CLOUD_WORKDIR, filename)
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_decision_engine(client):
    kill_application(client, 'decision')

def _start_cep_application(client, application):
    cmd = 'sudo systemctl start {}'.format(application)
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_cep_application(client):
    kill_application(client, 'java')

def _start_analytics(client):
    cmd = 'cd analytics && source ./env/bin/activate && python -m main > analytics.txt 2>&1 &'
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_analytics(client):
    kill_application(client, 'python')

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
    publisher.publish_application_name(name)

'''
    Experiment Orchestration
'''

def run_experiment(edgeClient, cloudClient):
    number_of_executions = 30
    # TODO: add loop for internal replications (30 executions for increasing statistical power)

    _start_analytics(edgeClient)
    _start_edge_profiler(edgeClient, 0)
    _start_cloud_profiler(cloudClient, 0)

    for application in APPLICATIONS:
        print('Running experiment for application: {}'.format(application))

        _start_cep_application(edgeClient, application)
        _start_edge_decision_engine(edgeClient)
        _start_cloud_decision_engine(cloudClient)

        sleep(5)

        mqtt.start()
        _publish_application_name(application)
        mqtt.stop()

        sleep(2 * 60)

        mqtt.start()
        publish_workload_data(publisher, DATA_THROUGHPUT_FACTORS, NUMBER_OF_EVENTS_TO_PUBLISH)
        mqtt.stop()

        # print('\tReceiving logs from nodes')

        # _get_profiler_logs(cloudClient, '/'+CLOUD_WORKDIR)
        # _process_profiler_logs(filename)
        # _save_flink_overall_metrics(job_id, 0, application)

        print('\tDone')

        _stop_cep_application(edgeClient)
        _stop_decision_engine(edgeClient)
        _stop_decision_engine(cloudClient)

        get_logs(edgeClient, EDGE_WORKDIR, LOG_FILE_NAME_FORMAT, RAW_DATA_LOGS_OUTPUT_DIR)
        get_logs(cloudClient, CLOUD_WORKDIR, LOG_FILE_NAME_FORMAT, RAW_DATA_LOGS_OUTPUT_DIR)

        print('\n')

    _stop_profiler(edgeClient)
    _stop_profiler(cloudClient)
    _stop_analytics(edgeClient)


# --------------- graphs

edgeClient = start_ssh_connection(EDGE_NODE_HOSTNAME, EDGE_NODE_SSH_USERNAME)
cloudClient = start_ssh_connection(CLOUD_NODE_HOSTNAME, CLOUD_NODE_SSH_USERNAME)

def signal_handler(sig, frame):
    print('Exiting gracefully')
    mqtt.stop()
    _stop_profiler(edgeClient)
    _stop_profiler(cloudClient)
    _stop_cep_application(edgeClient)
    _stop_decision_engine(edg33eClient)
    _stop_decision_engine(cloudClient)
    _stop_analytics(edgeClient)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
run_experiment(edgeClient, cloudClient)
cloudClient.close()

# TODO: 1. adicionar categorizacaoo das colunas e gerar CSV consolidado dos dados.
# TODO: 2. adicionar coleta de metricas gerais do CEP (DONE)
# TODO: 3. adicionar processamento de CSVs pra gerar imagens com Python mesmo
    # - grafico de linha, calculo de dis. normal, metricas como media, mediana, etc, etc
# TODO: 4. adicionar um arquivo com as execuções, intervalos de tempos e fatores envolvidos no experimento
# e.g. 0 -> profiler -> f0.001 -> between 23h and 1h

# TODO: 5. diferenciar execucoes de teste de execucoes reais: lifecycle do flink é gerenciado pelo decision engine