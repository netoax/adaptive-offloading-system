package runner

import (
	"fmt"
	"io/ioutil"
	"log"

	"github.com/netoax/adaptive-offloading-system/decision/pkg/flink"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/mqtt"
)

type Cloud struct {
	subscriber *mqtt.MessageSubscriber
	publisher  *mqtt.MessagePublisher
	flink      *flink.Flink
}

func NewCloud(subscriber *mqtt.MessageSubscriber, publisher *mqtt.MessagePublisher, flink *flink.Flink) *Cloud {
	return &Cloud{subscriber, publisher, flink}
}

func (c *Cloud) Start() {
	c.subscriber.OnOffloadingRequest(c.handleOffloadingRequest)
	c.subscriber.OnOffloadingStateSent(c.handleOffloadingState)
	c.subscriber.OnOffloadingStopReq(c.handleOffloadingStopReq)

	// incoming workload data
	c.subscriber.OnApplicationData(c.handleApplicationData)
}

func (c *Cloud) handleOffloadingRequest(payload string, topic string) {
	log.Println("cloud: offloading request received")
	c.publisher.PublishOffloadingAllowed()
	log.Println("cloud: offloading allowed")
}

func (c *Cloud) handleOffloadingState(payload string, topic string) {
	log.Println("cloud: offloading state received")
	// log.Println(payload)

	err := ioutil.WriteFile("/tmp/engine/state", []byte(payload), 0644)
	if err != nil {
		fmt.Println(err)
		log.Println("cloud: failed to write state file")
		return
	}

	err = c.flink.RunJob("/tmp/engine/state")
	if err != nil {
		log.Println("cloud: failed to start the job: ", err)
		return
	}

	c.publisher.PublishOffloadingStateConfirm()
	log.Println("cloud: offloading state confirmed")
}

func (c *Cloud) handleOffloadingStopReq(payload string, topic string) {
	log.Println("cloud: offloading stop request received")

	state, err := c.flink.GetState()
	if err != nil {
		log.Println("cloud: cannot extract state")
	}

	c.flink.StopJob()

	// c.flink.RunJob("/tmp/savepoints/savepoint-59a4fe-ce40e16924a0")

	c.publisher.PublishOffloadingStopConfirm(state)
	log.Println("cloud: offloading stop confirmed: sending state")
}

func (c *Cloud) handleApplicationData(payload, topic string) {
	// context := &PoliciesContext{}
	// json.Unmarshal([]byte(payload), context)

	// e.policiesCtx = context

	log.Println("cloud: application data received: processing locally")
	c.publisher.PublishLocalApplicationData(topic, payload)
}
