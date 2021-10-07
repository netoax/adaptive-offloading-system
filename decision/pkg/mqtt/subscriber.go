package mqtt

import (
	MQTT "github.com/eclipse/paho.mqtt.golang"
)

// MessageSubscriber ...
type MessageSubscriber struct {
	mode   string
	local  *Broker
	remote *Broker
}

// NewSubscriber ...
func NewSubscriber(mode string, local *Broker, remote *Broker) *MessageSubscriber {
	return &MessageSubscriber{mode, local, remote}
}

func (p *MessageSubscriber) OnOffloadingSignal(handler func(string, string)) error {
	return p.Subscribe(p.local, offloadingSignal, handler)
}

func (p *MessageSubscriber) OnOffloadingRequest(handler func(string, string)) error {
	return p.Subscribe(p.local, offloadingRequest, handler)
}

func (p *MessageSubscriber) OnOffloadingAllowed(handler func(string, string)) error {
	return p.Subscribe(p.remote, offloadingAllowed, handler)
}

func (p *MessageSubscriber) OnOffloadingStateSent(handler func(string, string)) error {
	return p.Subscribe(p.local, offloadingStateSubmission, handler)
}

func (p *MessageSubscriber) OnOffloadingStateConfirmed(handler func(string, string)) error {
	return p.Subscribe(p.remote, offloadingStateConfirmed, handler)
}

func (p *MessageSubscriber) OnOffloadingStopReq(handler func(string, string)) error {
	return p.Subscribe(p.local, offloadingStopRequest, handler)
}

func (p *MessageSubscriber) OnOffloadingStopConfirmed(handler func(string, string)) error {
	return p.Subscribe(p.remote, offloadingStopConfirmed, handler)
}

func (p *MessageSubscriber) OnPolicyStatusUpdate(handler func(string, string)) error {
	return p.Subscribe(p.local, policyStatusUpdate, handler)
}

func (p *MessageSubscriber) OnConceptDrift(handler func(string, string)) error {
	return p.Subscribe(p.local, conceptDriftOccurrence, handler)
}

func (p *MessageSubscriber) OnApplicationData(handler func(string, string)) error {
	return p.Subscribe(p.local, dataSent, handler)
}

func (p *MessageSubscriber) OnApplicationName(handler func(string, string)) error {
	return p.Subscribe(p.local, applicationName, handler)
}

func (p *MessageSubscriber) OnProfilingMetrics(handler func(string, string)) error {
	return p.Subscribe(p.local, profilingMetrics, handler)
}

// Subscribe ...
func (p *MessageSubscriber) Subscribe(broker *Broker, topic string, handler func(string, string)) error {
	messageHandler := func(client MQTT.Client, msg MQTT.Message) {
		handler(string(msg.Payload()), msg.Topic())
	}

	token := broker.client.Subscribe(topic, 0, messageHandler)
	if token.Error() != nil {
		return token.Error()
	}

	return nil
}
