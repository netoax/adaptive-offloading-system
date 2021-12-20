BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

DATA_THROUGHPUT_FACTORS = [250, 500, 750]
NUMBER_OF_EVENTS_TO_PUBLISH = '100000'
CHUNK_SIZE = 100000

RAW_DATA_LOGS_OUTPUT_DIR = '/Users/jneto/msc/workspace/results/staging'

CEP_APPLICATION_SIMPLE = 'ddos-10s'
CEP_APPLICATION_COMPLEX = 'ddos-128s'

MACHINE_LEARNING_ENABLED = True

APPLICATIONS = ['ddos-10s']

EXPERIMENT_EXECUTION_TIME = 30 # 30 minutes

NUMBER_OF_EXECUTIONS = 2

LOG_FILE_NAME_FORMAT = '*.nmon'
# RAW_DATA_LOGS_OUTPUT_DIR = './results/nmon/'

FLINK_CLUSTER_DIR = './apache-flink/apache-flink-1.10.0'

# SSH Connection

EDGE_NODE_HOSTNAME = '192.168.3.11'
EDGE_NODE_SSH_USERNAME = 'pi'
EDGE_WORKDIR = '/home/pi/'
EDGE_CEP_PORT = 8282

CLOUD_NODE_HOSTNAME = '34.235.137.114'
CLOUD_NODE_SSH_USERNAME = 'ec2-user'
CLOUD_WORKDIR = '/home/ec2-user/'
CLOUD_CEP_PORT = 8081

EDGE_INFO = {
    "hostname": EDGE_NODE_HOSTNAME,
    "username": EDGE_NODE_SSH_USERNAME,
    "workdir": EDGE_WORKDIR,
}

CLOUD_INFO = {
    "hostname": CLOUD_NODE_HOSTNAME,
    "username": CLOUD_NODE_SSH_USERNAME,
    "workdir": CLOUD_WORKDIR,
}

LOAD_EXPERIMENTS_NODES = {
    "edge": EDGE_INFO,
    # "cloud": CLOUD_INFO,
}