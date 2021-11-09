from analytics.network.mqtt import MQTT
from analytics.network.publisher import MessagePublisher
from analytics.network.subscriber import MessageSubscriber

received_response_events = [0]

mqtt = MQTT(hostname='192.168.3.11', port=1883)
subscriber = MessageSubscriber(mqtt)
mqtt.start()

def start_response_count(counter=[0]):
    def count_received_response_data(mosq, obj, msg):
        counter[0] += 1
        print(counter[0])

    subscriber.on_cep_response(count_received_response_data)

start_response_count(received_response_events)
mqtt.loop_forever()