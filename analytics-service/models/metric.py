import json
from dataclasses import dataclass
import numpy as np
from skmultiflow.data import DataStream

@dataclass
class Measurement:
    cep_latency: float = 0.0
    cpu: float = 0.0
    memory: float = 0.0
    bandwidth: float = 0.0

    def is_complete(self):
        print(self)
        if self.cep_latency and self.cpu and self.memory and self.bandwidth:
            return True
        return False

    def to_stream(self):
        instance = np.array([[self.cep_latency, self.cpu, self.memory, self.bandwidth, 0]])
        stream = DataStream(instance, n_targets=1, target_idx=-1)
        stream.prepare_for_use()
        X, Y = stream.next_sample()
        return X

    def fill_from_dict(self, data):
        self.cep_latency = data['cep_latency']
        self.cpu = data['cpu']
        self.memory = data['memory']
        self.bandwidth = data['bandwidth']