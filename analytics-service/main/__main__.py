from network.mqtt import MQTT
from network.publisher import MessagePublisher
from network.subscriber import MessageSubscriber
from training.trainer import Trainer
from classification.classifier import Classifier
from stream.processor import Processor
from init_logger import init_logger

import signal
import sys

logger = init_logger(__name__, testing_mode=False)

mqtt = MQTT()
publisher = MessagePublisher(mqtt)
subscriber = MessageSubscriber(mqtt)
processor = Processor(subscriber, init_logger("stream-processor", testing_mode=False))

def classification_result(result):
    logger.info("model: classification: " + result)
    publisher.publish_offloading_prediction(result)

model = "HoeffdingTree"
trainer = Trainer(model, init_logger("training", testing_mode=False))
classifier = Classifier(trainer.get_trained_model(), publisher, init_logger("classification", testing_mode=False))
classifier.on_classification(classification_result)
processor.on_instance(classifier.predict)
processor.on_assessment(trainer.fit)

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

mqtt.start()
processor.start()
mqtt.loop_forever()