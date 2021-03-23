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
        self.__measurement = Measurement()

    def start(self):
        self.__subscriber.on_device_metrics(self._device_metrics_callback)
        self.__subscriber.on_cep_metrics(self._cep_metrics_callback)
        self.__subscriber.on_assessment(self._assessment_callback)

    def on_instance(self, callback):
        self.__instance_callback = callback

    def on_assessment(self, callback):
        self.__assessment_callback = callback

    def _prepare_measurement_sample(self, measurement):
        instance = np.array([[measurement.latency, measurement.cpu, measurement.memory]])
        stream = DataStream(instance, n_targets=1, target_idx=-1)
        stream.prepare_for_use()
        X, Y = stream.next_sample()
        return X

    def _assessment_callback(self, mosq, obj, msg):
        data = json.loads(msg.payload)
        measurement = Measurement(data.get("latency"), data.get("cpu"), data.get("memory"))
        sample = self._prepare_measurement_sample(measurement)
        status = data.get("correct")
        self.__assessment_callback(sample, bool(status))

    def _cep_metrics_callback(self, mosq, obj, msg):
        data = json.loads(msg.payload)
        self.__measurement.latency = float(data.get("metrics").get("latency"))

        if self.__measurement.is_complete():
            self.__logger.info("metrics: " + str(self.__measurement))
            self._process_stream()

    def _device_metrics_callback(self, mosq, obj, msg):
        data = json.loads(msg.payload)
        self.__measurement.cpu = data.get("cpu")
        self.__measurement.memory = data.get("memory")

        if self.__measurement.is_complete():
            self.__logger.info("metrics: " + str(self.__measurement))
            self._process_stream()

    def _process_stream(self):
        X = self._prepare_measurement_sample(self.__measurement)
        self.__instance_callback({
            "timestamp": str(datetime.datetime.utcnow()),
            "id": str(uuid.uuid4()),
            "sample": X
        })

