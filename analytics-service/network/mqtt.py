import paho.mqtt.client as mqtt

class MQTT():
    def __init__(self, hostname='localhost', port=1883):
        self.hostname = hostname
        self.port = port
        self.client = mqtt.Client()

    def start(self):
        self.client.on_connect = self.on_connected
        self.client.connect(self.hostname, self.port)

    def loop_forever(self):
        self.client.loop_forever()

    def on_connected(self, client, userdata, flags, rc):
        print("Connected to MQTT broker")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def subscribe(self, topic, callback):
        self.client.subscribe(topic, 0)
        self.client.message_callback_add(topic, callback)
