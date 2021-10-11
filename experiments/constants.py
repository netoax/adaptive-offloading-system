BOTNET_DATASET_USED_COLUMNS = ['stime', 'proto', 'saddr', 'sport', 'daddr', 'dport', 'bytes', 'state']
BOTNET_DATASET_COLUMNS_DATA_TYPE = {'stime': float, 'proto': str, 'saddr': str, 'daddr': str, 'bytes': int, 'state': str}

DATA_THROUGHPUT_FACTORS = ['0.001']
NUMBER_OF_EVENTS_TO_PUBLISH = '500000'
CHUNK_SIZE = 100000
DATASET_PATH = './192.168.100.149.csv'
