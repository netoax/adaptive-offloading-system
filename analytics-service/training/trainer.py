import numpy as np

from skmultiflow.trees import HoeffdingTree
from skmultiflow.data import DataStream
# from skmultiflow.drift_detection.adwin import ADWIN
# from skmultiflow.metrics import ClassificationMeasurements
from skmultiflow.metrics import ClassificationMeasurements

MODELS = {
    "HoeffdingTree": HoeffdingTree,
}

class Trainer():
    def __init__(self, model, logger):
        self._model = MODELS[model]()
        self.__logger = logger
        self.__metrics = ClassificationMeasurements([0,1], int)

    def get_trained_model(self):
        return self._model

    ## Create stream and prepare to be used
    def _prepare_stream(self, latency):
        instance = np.array([[latency]])
        stream = DataStream(instance, n_targets=1, target_idx=-1)
        stream.prepare_for_use()
        return stream

    # TODO: docstring
    def fit(self, sample, label):
        ## Update the model
        self._model.partial_fit(sample, [label])

        self.__logger.info("model trained with...")
        # self.metrics.add_result(label, prediction[0])
        # self.logger.info(self.metrics.get_info())

        print(self._model.get_model_measurements)

