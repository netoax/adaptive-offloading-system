class MessageSubscriber():
    def __init__(self, mqtt):
        self.mqtt = mqtt

    def on_device_metrics(self, callback):
        self.mqtt.subscribe('/metrics/device', callback)

    def on_cep_metrics(self, callback):
        self.mqtt.subscribe('/metrics/cep', callback)

    def on_assessment(self, callback):
        self.mqtt.subscribe('/assessment', callback)
