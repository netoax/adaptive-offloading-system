from network.mqtt import MQTT
from network.publisher import MessagePublisher
from network.subscriber import MessageSubscriber
from training.trainer import Trainer
from classification.classifier import Classifier
from drift.detector import Detector
from stream.processor import Processor
from init_logger import init_logger
from policy_manager import PolicyManager

import signal
import sys
import os
import json

external_assessment = os.environ.get('EXTERNAL_ASSESSMENT')
policy_only = os.environ.get('POLICY_ONLY')

logger = init_logger(__name__, testing_mode=False)

POLICIES_PATH = './policies.xml'
model = "HoeffdingTree"
detector = "ADWIN"

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    # Basic dependencies
    mqtt = MQTT()
    publisher = MessagePublisher(mqtt)
    subscriber = MessageSubscriber(mqtt)
    processor = Processor(subscriber, init_logger("stream-processor", testing_mode=False))
    policy_manager = PolicyManager(POLICIES_PATH, logger, publisher)

    if policy_only:
        start_policy(processor, policy_manager)
    else:
        start_analytics(publisher, processor, policy_manager)

    mqtt.start()
    processor.start()
    mqtt.loop_forever()

def start_policy(processor, policy_manager):
    processor.on_measurement_instance(policy_manager.is_policy_violated)

def drift_detected():
    publisher.publish_detected_drift()

def start_analytics(publisher, processor, policy_manager):
    trainer = Trainer(model, init_logger("training", testing_mode=False), external_assessment, publisher, policy_manager)
    classifier = Classifier(trainer.get_trained_model(), publisher, init_logger("classification", testing_mode=False))
    drift_detector = Detector(detector, trainer, init_logger("detector", testing_mode=False))
    processor.on_instance(classifier.predict)

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
        publisher.publish_offloading_prediction(json.dumps(result_tmp))

    classifier.on_classification(classification_result)
    drift_detector.on_drift_detected(drift_detected)

main()
