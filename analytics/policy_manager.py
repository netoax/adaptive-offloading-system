import xml.dom.minidom
import inspect
import json

from analytics.network.publisher import MessagePublisher
from analytics.network.mqtt import MQTT
from analytics.models.metric import Measurement

class PolicyManager():
    def __init__(self, path, logger, publisher):
        self.doc = xml.dom.minidom.parse(path)
        self.__logger = logger
        self.__publisher = publisher
        self.params = {}
        self.composed = {}
        self.process()

    def process(self):
        policies = self.doc.getElementsByTagName("policy")
        for policy in policies:
            if policy.getAttribute("type") == "composed":
                rules = policy.getElementsByTagName("rule")
                for rule in rules:
                    self.composed[rule.getAttribute("name")] = rule.getAttribute("value")
            else:
                self.params[policy.getAttribute("name")] = {
                    "value": policy.getAttribute("value"),
                    "repetitions": int(policy.getAttribute("repetitions")) if policy.getAttribute("repetitions") else 1,
                    "count": 0
                }
                print(self.params)

    def is_policy_violated(self, measurement):
        status = {
            "violated": False
        }
        if self.is_composed_violated(measurement) or self.is_simple_violated(measurement):
            self.__logger.info('resource policy violated')
            status["violated"] = True
            self.__publisher.publish_policy_violation(json.dumps(status))
            return True

        self.__publisher.publish_policy_violation(json.dumps(status))
        return False

    def is_simple_violated(self, measurement):
        for key, value in self.params.items():
            metric_value = measurement.get(key)

            is_violated = metric_value > float(value["value"])
            repetitions_expected = value["repetitions"]
            repetitions_actual = value["count"]

            if is_violated:
                if repetitions_expected == 1:
                    return True
                if repetitions_actual == repetitions_expected:
                    return True

                self.params[key]['count'] += 1
                print("count incremented: ", self.params[key]['count'])
        return False

    def is_composed_violated(self, measurement):
        violation_control = False
        for key, value in self.composed.items():
            metric_value = measurement.get(key)
            if metric_value > float(value):
                violation_control = violation_control and True
            else:
                violation_control = False
        return violation_control

# mqtt = MQTT(hostname="192.168.3.11", port=1883)
# mqtt.start()
# publisher = MessagePublisher(mqtt)
# policy_manager = PolicyManager("/Users/jneto/msc/workspace/adaptive-offloading-system/analytics/policies.xml", None, publisher)
# policy_manager.process()

# m = Measurement(cpu=45)

# result = policy_manager.is_policy_violated(m.to_dict())
# result = policy_manager.is_policy_violated(m.to_dict())
# result = policy_manager.is_policy_violated(m.to_dict())

# print(result)