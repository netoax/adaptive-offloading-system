import numpy as np
import uuid
import datetime
from skmultiflow.data import DataStream
import json
from models.metric import Measurement


class Processor():
    def __init__(self, subscriber, logger):
        self.__subscriber = subscriber
        self.__logger = logger

    def start(self):
        self.__subscriber.on_metrics(self._metrics_callback)

    def on_instance(self, callback):
        self.__instance_callback = callback

    def on_assessment(self, callback):
        self.__assessment_callback = callback

    def on_assessment_result(self, callback):
        self.__assessment_result_callback = callback

    def _metrics_callback(self, mosq, obj, msg):
        data = json.loads(msg.payload)
        m = Measurement(
            float(data.get("cepLatency")),
            data.get("cpu"),
            data.get("memory"),
            data.get("bandwidth")
        )
        self._process_stream(m)

    def _prepare_measurement_sample(self, measurement):
        instance = np.array([[measurement.cep_latency, measurement.cpu, measurement.memory, 0]])
        stream = DataStream(instance, n_targets=1, target_idx=-1)
        stream.prepare_for_use()
        X, Y = stream.next_sample()
        return X

    def _assessment_callback(self, mosq, obj, msg):
        data = json.loads(msg.payload)
        measurement = Measurement(data.get("latency"), data.get("cpu"), data.get("memory"))
        status = data.get("correct")
        prediction = data.get("prediction")
        self.__assessment_result_callback(status)
        self.__assessment_callback(measurement.to_stream(), bool(status), prediction)

    def _process_stream(self, measurement):
        self.__instance_callback({
            "timestamp": str(datetime.datetime.utcnow()),
            "id": str(uuid.uuid4()),
            "sample": measurement.to_stream(),
        })
