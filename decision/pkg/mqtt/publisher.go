package mqtt

import "strconv"

type Publisher interface {
	Publish(topic string, data interface{}) error
}

type MessagePublisher struct {
	local  *Broker
	remote *Broker
}

func NewPublisher(local *Broker, remote *Broker) *MessagePublisher {
	return &MessagePublisher{local, remote}
}

func (p *MessagePublisher) PublishOffloadingAllowed(status bool) error {
	st := strconv.FormatBool(status)
	return p.Publish(p.local, offloadingAllowed, st)
}

func (p *MessagePublisher) PublishOffloadingRequest() error {
	return p.Publish(p.remote, offloadingRequest, "")
}

func (p *MessagePublisher) PublishOffloadingState(state []byte) error {
	return p.Publish(p.remote, offloadingStateSubmission, string(state))
}

func (p *MessagePublisher) PublishOffloadingStateConfirm() error {
	return p.Publish(p.local, offloadingStateConfirmed, "")
}

func (p *MessagePublisher) PublishOffloadingStop() error {
	return p.Publish(p.remote, offloadingStopRequest, "")
}

func (p *MessagePublisher) PublishOffloadingStopConfirm(state []byte) error {
	return p.Publish(p.local, offloadingStopConfirmed, string(state))
}

func (p *MessagePublisher) PublishRemoteApplicationData(topic, payload string) error {
	return p.Publish(p.remote, topic, payload)
}

func (p *MessagePublisher) PublishLocalApplicationData(topic, payload string) error {
	return p.Publish(p.local, "/cep"+topic, payload)
}

func (p *MessagePublisher) PublishJobID(payload string) error {
	return p.Publish(p.local, "/profiling/job/id", payload)
}

func (p *MessagePublisher) Publish(broker *Broker, topic string, data interface{}) error {
	token := broker.client.Publish(topic, 1, false, data)
	if token.Error() != nil {
		return token.Error()
	}

	return nil
}
