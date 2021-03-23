import json

class Classifier():
    def __init__(self, model, publisher, logger):
        self.__model = model
        self.__publisher = publisher
        self.__logger = logger

    def on_classification(self, callback):
        self.__classification_callback = callback

    def predict(self, instance):
        # print(instance)
        result = self.__model.predict(instance['sample'])
        # print("classification")
        # print(result[0])

        result = {
            'model': "HoeffdingTree", # Get from model
            'result': bool(result[0])
        }

        self.__classification_callback(json.dumps(result))