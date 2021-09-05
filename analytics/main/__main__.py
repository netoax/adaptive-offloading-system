from network.mqtt import MQTT
from network.publisher import MessagePublisher
from network.subscriber import MessageSubscriber
from training.trainer import Trainer
from classification.classifier import Classifier
from drift.detector import Detector
from stream.processor import Processor
from init_logger import init_logger

import signal
import sys
import os
import json

external_assessment = os.environ.get('EXTERNAL_ASSESSMENT')

logger = init_logger(__name__, testing_mode=False)

mqtt = MQTT()
publisher = MessagePublisher(mqtt)
subscriber = MessageSubscriber(mqtt)
processor = Processor(subscriber, init_logger("stream-processor", testing_mode=False))

model = "HoeffdingTree"
detector = "ADWIN"
trainer = Trainer(model, init_logger("training", testing_mode=False), external_assessment, publisher)
classifier = Classifier(trainer.get_trained_model(), publisher, init_logger("classification", testing_mode=False))
drift_detector = Detector(detector, trainer, init_logger("detector", testing_mode=False))
processor.on_instance(classifier.predict)
# processor.add_instance_callback(policy_manager.is_policy_violated)

if external_assessment:
    processor.on_assessment(trainer.fit)
    processor.on_assessment_result(drift_detector.fit)

def classification_result(result):
    if not external_assessment:
        trainer.internal_fit(result)
        drift_detector.fit(result)

    logger.info("model: classification: {}".format(result))
    result_tmp = trainer.get_metrics()
    result_tmp =  { **result_tmp, "status": result["result"] }
    print(result_tmp)
    publisher.publish_offloading_prediction(json.dumps(result_tmp))

def drift_detected():
    publisher.publish_detected_drift()

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
classifier.on_classification(classification_result)
drift_detector.on_drift_detected(drift_detected)

mqtt.start()
processor.start()
mqtt.loop_forever()