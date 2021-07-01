import xml.dom.minidom
import inspect
import json

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
                self.params[policy.getAttribute("name")] = policy.getAttribute("value")

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
            if metric_value > float(value):
                return True
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
