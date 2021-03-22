package mqtt

import "fmt"

// Publisher ...
type Publisher interface {
	Publish(topic string, data interface{}) error
}

// MessagePublisher ...
type MessagePublisher struct {
	broker Broker
}

// NewPublisher ...
func NewPublisher(broker Broker) *MessagePublisher {
	return &MessagePublisher{broker}
}

// Publish ...
func (p *MessagePublisher) Publish(topic string, data interface{}) error {
	token := p.broker.client.Publish(topic, 0, false, data)
	if token.Error() != nil {
		fmt.Println(token.Error())
		return token.Error()
	}

	return nil
}
