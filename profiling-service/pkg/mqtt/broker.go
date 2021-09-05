package mqtt

import (
	MQTT "github.com/eclipse/paho.mqtt.golang"
)

// Broker ...
type Broker struct {
	address string
	topic   string
	client  MQTT.Client
}

// NewBroker ...
func NewBroker(address string, topic string) *Broker {
	return &Broker{address, topic, nil}
}

// Start ...
func (b *Broker) Start() error {
	opts := MQTT.NewClientOptions()
	opts.SetAutoReconnect(true)
	opts.AddBroker(b.address)
	client := MQTT.NewClient(opts)
	token := client.Connect()
	if token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	// log.Println("successfully connected to MQTT broker")
	b.client = client
	return nil
}
