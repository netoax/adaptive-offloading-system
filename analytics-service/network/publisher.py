import json

class MessagePublisher():
    def __init__(self, mqtt):
        self.mqtt = mqtt

    def send_cep_control_data(self, payload):
        self.mqtt.publish('/context/cep/control', payload)

    def publish_offloading_prediction(self, payload):
        self.mqtt.publish('/prediction/offloading', payload)

    def publish_detected_drift(self):
        self.mqtt.publish('/drift/detected')