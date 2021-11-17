# Targets: edge, cloud
# Workload: same
# Application: simple, complex
# Throughput: 5000 m/s
# Metrics: CPU, memory, bandwidth, latência do CEP, data from one attacker

from time import sleep
from rich import print

from experiments.data import *
from experiments.ssh import *
from experiments.flink import *

from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher
from analytics.network.subscriber import MessageSubscriber

from experiments.constants import *

SLEEP_INTERVAL_SECONDS = 80

def run_load_experiment(client, mqtt, publisher, subscriber, application, hostname, workdir):
    print('loading test:', application)
    start_nmon(client)
    # mqtt.start()

    for factor in DATA_THROUGHPUT_FACTORS:
        sleep(10)
        start_cep_application(client, application)
        sleep(SLEEP_INTERVAL_SECONDS)
        n1 = get_number_of_starts_cep(client)

        publish_workload_data(publisher, subscriber, [factor], hostname, EXPERIMENT_EXECUTION_TIME)

        sleep(10)
        get_logs(client, workdir, LOG_FILE_NAME_FORMAT, RAW_DATA_LOGS_OUTPUT_DIR)
        # response = save_flink_overall_metrics(EDGE_NODE_HOSTNAME, n, CEP_APPLICATION)
        # parsed_response = _parse_flink_response(response)
        n2 = get_number_of_starts_cep(client)

        stop_cep_application(client, application)
        sleep(15)
        kill_application(client, 'nmon')

        print('\trestarts: ', n2 - n1)
        print('\n')

    # mqtt.stop()

def run_node_execution(node, info):
    print('target:', node)
    ssh = start_ssh_connection(info['hostname'], info['username'])
    mqtt_pub = MQTT(hostname=info['hostname'], port=1883)
    mqtt_sub = MQTT(hostname=info['hostname'], port=1883)

    mqtt_pub.start()
    mqtt_sub.start()

    publisher = MessagePublisher(mqtt_pub)
    subscriber = MessageSubscriber(mqtt_sub)

    # run_load_experiment(ssh, mqtt_sub, publisher, subscriber, CEP_APPLICATION_COMPLEX, info['hostname'], info['workdir'])
    run_load_experiment(ssh, mqtt_sub, publisher, subscriber, CEP_APPLICATION_SIMPLE, info['hostname'], info['workdir'])

def start_experiment():
    for node in LOAD_EXPERIMENTS_NODES:
        run_node_execution(node, LOAD_EXPERIMENTS_NODES[node])

start_experiment()