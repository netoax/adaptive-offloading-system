package mqtt

import (
	"fmt"

	MQTT "github.com/eclipse/paho.mqtt.golang"
)

// Subscriber ...
type Subscriber interface {
	Subscribe(topic string, data interface{}) error
}

// MessageSubscriber ...
type MessageSubscriber struct {
	broker Broker
}

// NewSubscriber ...
func NewSubscriber(broker Broker) *MessageSubscriber {
	return &MessageSubscriber{broker}
}

// Subscribe ...
func (p *MessageSubscriber) Subscribe(topic string, handler func(string)) error {
	messageHandler := func(client MQTT.Client, msg MQTT.Message) {
		handler(string(msg.Payload()))
	}

	token := p.broker.client.Subscribe(topic, 0, messageHandler)
	if token.Error() != nil {
		fmt.Println(token.Error())
		return token.Error()
	}

	return nil
}
