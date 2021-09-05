import numpy as np
import json

from skmultiflow.trees import HoeffdingTree
from skmultiflow.data import DataStream
from skmultiflow.metrics import ClassificationMeasurements
from policy_manager import PolicyManager
from models.metric import Measurement

MODELS = {
    "HoeffdingTree": HoeffdingTree,
}

POLICIES_PATH = './policies.xml'

class Trainer():
    def __init__(self, model, logger, external_assessment, publisher):
        self.__model = MODELS[model]()
        self.__logger = logger
        self.__metrics = ClassificationMeasurements([0,1], int)
        self.__external_assessment = external_assessment
        self.__policy_manager = PolicyManager(POLICIES_PATH, logger, publisher)

    def get_trained_model(self):
        return self.__model

    ## Create stream and prepare to be used
    def _prepare_stream(self, latency):
        instance = np.array([[latency]])
        stream = DataStream(instance, n_targets=1, target_idx=-1)
        stream.prepare_for_use()
        return stream

    def reset(self):
        self.__model.reset()

    def internal_fit(self, classification):
        measurement = Measurement()
        measurement.fill_from_dict(classification['instance'])
        result = self.__policy_manager.is_policy_violated(classification['instance'])
        self.fit(measurement.to_stream(), result, classification['result'])

    def get_metrics(self):
        return self.__dict_metrics

    # TODO: docstring
    def fit(self, sample, label, result):
        ## Update the model
        self.__model.partial_fit(sample, [label])
        self.__logger.info("model trained with {}".format(label))
        self.__metrics.add_result(label, result)
        print(self.__metrics)
        self.__dict_metrics = {
            "f1-score": self.__metrics.get_f1_score(),
            "kappa": self.__metrics.get_kappa(),
            "accuracy": self.__metrics.get_accuracy(),
            "precision": self.__metrics.get_precision(),
            "recall": self.__metrics.get_recall(),
        }

        self.__logger.info(self.__dict_metrics)

