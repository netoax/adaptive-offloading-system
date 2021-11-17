import json

class MessagePublisher():
    def __init__(self, mqtt):
        self.mqtt = mqtt

    def send_cep_control_data(self, payload):
        self.mqtt.publish('/context/cep/control', payload)

    def publish_offloading_prediction(self, payload):
        self.mqtt.publish('/prediction/offloading', payload)

    def publish_offloading_response(self, payload):
        self.mqtt.publish('/offloading/request/allowed', "")

    def publish_state_response(self, payload):
        self.mqtt.publish('/offloading/state/confirmed', "")

    def publish_stop_response(self, payload):
        self.mqtt.publish('/offloading/stop/confirmed', "")

    def publish_detected_drift(self):
        self.mqtt.publish('/prediction/drift', json.dumps({'a':1}))

    def publish_traffic_data(self, payload):
        self.mqtt.publish('/application/traffic/data', payload)

    def publish_network_data(self, payload):
        self.mqtt.publish('/application/network/data', payload)

    def publish_weather_data(self, payload):
        self.mqtt.publish('/application/weather/data', payload)

    def publish_profiling_data(self, payload):
        self.mqtt.publish('/profiling/metrics', payload)

    def publish_policy_violation(self, payload):
        self.mqtt.publish('/policies/status', payload)

    def publish_application_name(self, payload):
        self.mqtt.publish('/application/name', payload)

    def publish_job_id(self, payload):
        self.mqtt.publish('/application/name', payload)
