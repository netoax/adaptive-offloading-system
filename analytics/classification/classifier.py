import json

class Classifier():
    def __init__(self, model, publisher, logger):
        self.__model = model
        self.__publisher = publisher
        self.__logger = logger

    def on_classification(self, callback):
        self.__classification_callback = callback

    def _get_instance(self, ndarray):
        return {
            'cep_latency': ndarray['sample'][0][0],
            'cpu':ndarray['sample'][0][1],
            'memory': ndarray['sample'][0][2],
            'bandwidth': ndarray['sample'][0][3]
        }

    def predict(self, instance):
        result = self.__model.predict(instance['sample'])
        result = {
            'model': "HoeffdingTree", # Get from model
            'result': bool(result[0]),
            'instance': self._get_instance(instance)
        }

        self.__logger.info("prediction result is {}".format(result['result']))
        self.__classification_callback(result)