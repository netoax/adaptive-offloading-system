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

PROFILER_RESULTS_DIRECTORY = './results/profiler'
PROFILER_LOG_FILE_NAME_FORMAT = 'profiler-*.txt'

APPLICATIONS = ['ddos-10s', 'ddos-128s']

BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

# DATA_THROUGHPUT_FACTORS = ['0.001', '0.001', '0.0001', '0.00001', '0.0']
DATA_THROUGHPUT_FACTORS = ['0.00001', '0.0']
NUMBER_OF_EVENTS_TO_PUBLISH = '50000'

# EXECUTION_MODE = os.environ.get('EXECUTION_MODE') || 'test'

mqtt_local_hostname = '192.168.3.11'
mqtt = MQTT(hostname=mqtt_local_hostname, port=1883)

publisher = MessagePublisher(mqtt)
# mqtt.start()

logger = init_logger(__name__, testing_mode=False)
policy_manager = PolicyManager('./analytics/policies.xml', logger, publisher)

def _kill_application(client, application):
    stdin, stdout, stderr = client.exec_command('pgrep {}'.format(application))
    output = ''
    for line in stdout.readlines():
        output += line
    pid = output.strip('\n')
    client.exec_command('kill -9 {}'.format(pid))

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

def publish_botnet_data(factor='5', number='100000', chunk='100000'):
    reader = pd.read_csv(
        './test.csv',
        usecols=BOTNET_DATASET_USED_COLUMNS,
        dtype=BOTNET_DATASET_COLUMNS_DATA_TYPE,
        nrows=int(number),
        chunksize=100000
    )
    now = time.time()
    count = 0
    for df in reader:
        df = df.dropna()
        df = df[df['sport'] != '0x0303']
        df = df[df['dport'] != '0x5000']
        for index, row in df.iterrows():
            try:
                count = count + 1
                data = _from_row_to_dict(row)
                publisher.publish_network_data(json.dumps(data))
                time.sleep(float(factor))
            except Exception as ex:
                print(ex)
    elapsed = time.time() - now
    print('\tpublished {} events in {} seconds/minutes'.format(count, elapsed))
    print('\tthroughput: {}'.format(count / elapsed))

def _get_cep_job_id():
    r = requests.get('http://{}:8282/jobs'.format(EDGE_NODE_HOSTNAME))
    response = r.json()
    return response['jobs'][0]['id']

def _start_ssh_connection(hostname, user):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, 22, user)
    return client

def _start_profiler(client, execution_number, application):
    # filename = 'profiler-execution-{}-workload-{}-{}'.format(execution_number, application, datetime.now()).replace(" ", "")
    # job_id = _get_cep_job_id()
    cmd = 'export $(cat ./profiler.env) && export FLINK_JOB_ID={} && ./profiler > {}.txt 2>&1 &'.format(job_id, filename)
    stdin, stdout, stderr = client.exec_command(cmd)
    return filename, job_id

def _stop_profiler(client):
    _kill_application(client, 'profiler')

def _get_profiler_logs(client):
    file_path = '/home/pi/{}'.format(PROFILER_LOG_FILE_NAME_FORMAT)
    stdin, stdout, stderr = client.exec_command('ls {}'.format(file_path))
    result = stdout.read().split()
    scp = SCPClient(client.get_transport())
    for file in result:
        file = scp.get(file, PROFILER_RESULTS_DIRECTORY)

    client.exec_command('rm {}'.format(file_path))
    scp.close()

def _process_profiler_logs(filename):
    file = open('./results/profiler/{}.txt'.format(filename))
    next(file) # skip first line
    header = ['bandwidth', 'cepLatency', 'cpu', 'memory', 'rtt', 'timestamp']
    with open('./results/profiler/{}.csv'.format(filename), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for line in file:
            instance = json.loads(line)
            writer.writerow(instance.values())

def _start_decision_engine(client):
    cmd = 'export $(cat ./decision.env) && ./decision > decision.txt 2>&1 &'
    stdin, stdout, stderr = client.exec_command(cmd)
    # print(stdout)

def _stop_decision_engine(client):
    _kill_application(client, 'decision')

def _start_cep_application(client, application):
    cmd = 'sudo systemctl start {}'.format(application)
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_cep_application(client):
    _kill_application(client, 'java')

def _start_analytics(client):
    cmd = 'cd analytics && source ./env/bin/activate && python -m main &'
    stdin, stdout, stderr = client.exec_command(cmd)

def _stop_analytics():
    _kill_application(client, 'python')

def _save_flink_overall_metrics(job_id, execution_number, application):
    r = requests.get('http://{}:8282/jobs/{}'.format(EDGE_NODE_HOSTNAME, job_id))
    response = r.text
    file = open('./results/flink-execution-{}-workload-{}-{}.json'.format(execution_number, application, datetime.now()).replace(" ", ""), "w")
    file.write(response)
    file.close()

def _publish_workload_data():
    # publish_botnet_data('0.1', '500000')
    for f in DATA_THROUGHPUT_FACTORS:
        timestamp = datetime.now()
        print('\t{} - botnet workload: factor {}'.format(timestamp, f))
        publish_botnet_data(f, NUMBER_OF_EVENTS_TO_PUBLISH)
        # TODO: log information to metadata file
        # idle time
        timestamp = datetime.now()
        print('\t{} - botnet workload: idle time'.format(timestamp))
        time.sleep(5 * 60)

def run_experiment(client):
    number_of_executions = 30
    # TODO: add loop for internal replications (30 executions for increasing statistical power)

    _start_decision_engine(client)
    _start_analytics(client)
    _start_profiler(client, 0, application)

    for application in APPLICATIONS:
        # publish_botnet_data('0.1', '500000')
        print('Running experiment for {} with configured workload'.format(application))

        _start_cep_application(client, application)
        sleep(200)
        print('\tApplication started')


        filename, job_id = _start_profiler(client, 0, application)
        print('\tProfiler started')

        print('\tPublishing data to application')
        mqtt.start()
        _publish_workload_data()
        mqtt.stop()

        print('\tExecution logs received')
        _get_profiler_logs(client)

        print('\tExecution logs processed')
        _process_profiler_logs(filename)

        _stop_profiler(client)

        _save_flink_overall_metrics(job_id, 0, application)

        print('\tFinishing experiment')
        _stop_cep_application(client)

        print('\n')

    _stop_decision_engine(client)

# --------------- graphs

def create_line_charts_from_csv(columns=[]):
    pd.plotting.register_matplotlib_converters()

    fname = cbook.get_sample_data('/Users/jneto/msc/workspace/adaptive-offloading-system/data.csv', asfileobj=False)
    with cbook.get_sample_data('/Users/jneto/msc/workspace/adaptive-offloading-system/data.csv') as file:
        msft = pd.read_csv(file, parse_dates=['timestamp'])
        msft.plot("timestamp", ["cpu"], subplots=True)
        # msft.show()
        fig, ax = plt.subplots()
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.show()
        # plt.savefig('plot.png', dpi=300, bbox_inches='tight')


    # with open('file.csv') as file:
    #     line_reader = csv.reader(File)

    # data = np.genfromtxt("./data.csv", delimiter=",", names=["timestamp", "cpu"])
    # plt.plot(data['timestamp'], data['cpu'])

def statistical_tests():
    df = pd.read_csv('./data_2.csv')
    k2, p = stats.normaltest(df['memory'])
    alpha = 1e-3
    print(k2, p)
    if p < alpha:
        print("The null hypothesis can be rejected")
    else:
        print("The null hypothesis cannot be rejected")

def _label_columns():
    df = pd.read_csv('./analytics/random_data_test.csv')
    for index, row in df.iterrows():
        # print(row)
        measurement = Measurement(row['cepLatency'], row['cpu'], row['memory'], row['bandwidth'])
        # print(measurement)
        policy_manager.process()
        violated = policy_manager.is_composed_violated(measurement.to_dict()) or policy_manager.is_simple_violated(measurement.to_dict())
        # df['violated'] = int(violated)
        df.loc[index, 'violated'] = int(violated)
    df.to_csv('./random_data_labeled.csv', index=False)

# create_line_charts_from_csv()

# statistical_tests()
# _label_columns()

client = _start_ssh_connection(EDGE_NODE_HOSTNAME, EDGE_NODE_SSH_USERNAME)

def signal_handler(sig, frame):
    print('Exiting gracefully')
    mqtt.stop()
    _stop_profiler(client)
    _stop_cep_application(client)
    _stop_decision_engine(client)
    sys.exit(0)

# publish_botnet_data('0.1', '500000')
# sleep(15)
signal.signal(signal.SIGINT, signal_handler)
run_experiment(client)
# _save_flink_overall_metrics('69119a0c35183a9f20dfb2f7cdd5ee9d', 0, 'ddos.jar')
# _process_profiler_logs('profiler-execution-0-workload-ddos-128s.jar-2021-08-0519:23:08.382728')
client.close()

# TODO: 1. adicionar categorizacaoo das colunas e gerar CSV consolidado dos dados.
# TODO: 2. adicionar coleta de metricas gerais do CEP (DONE)
# TODO: 3. adicionar processamento de CSVs pra gerar imagens com Python mesmo
    # - grafico de linha, calculo de dis. normal, metricas como media, mediana, etc, etc
# TODO: 4. adicionar um arquivo com as execuções, intervalos de tempos e fatores envolvidos no experimento
# e.g. 0 -> profiler -> f0.001 -> between 23h and 1h

# TODO: 5. diferenciar execucoes de teste de execucoes reais: lifecycle do flink é gerenciado pelo decision engine