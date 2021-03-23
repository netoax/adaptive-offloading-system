import json
from dataclasses import dataclass

@dataclass
class Measurement:
    latency: float = 0.0
    cpu: float = 0.0
    memory: float = 0.0

    def is_complete(self):
        if self.latency and self.cpu and self.memory:
            return True
        return False
