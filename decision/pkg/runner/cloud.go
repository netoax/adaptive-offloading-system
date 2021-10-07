package runner

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"time"

	"github.com/netoax/adaptive-offloading-system/decision/pkg/flink"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/mqtt"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/state"
)

const (
	stateDirectory = "/tmp/state"
	parallelism    = "4"
)

type localContext struct {
	CPU       float64 `json:"cpu"`
	Memory    float64 `json:"memory"`
	Bandwidth float64 `json:"bandwidth"`
	CepLateny float64 `json:"cepLatency"`
}

type Cloud struct {
	subscriber  *mqtt.MessageSubscriber
	publisher   *mqtt.MessagePublisher
	flink       *flink.Flink
	application string
	state       *state.State
	context     *localContext
}

func NewCloud(subscriber *mqtt.MessageSubscriber, publisher *mqtt.MessagePublisher, flink *flink.Flink) *Cloud {
	state := state.NewState("cloud")
	return &Cloud{subscriber, publisher, flink, "", state, nil}
}

func (c *Cloud) Start() {
	c.subscriber.OnOffloadingRequest(c.handleOffloadingRequest)
	c.subscriber.OnOffloadingStateSent(c.handleOffloadingState)
	c.subscriber.OnOffloadingStopReq(c.handleOffloadingStopReq)

	// contextual data
	c.subscriber.OnProfilingMetrics(c.handleProflingMetrics)

	// incoming workload data
	c.subscriber.OnApplicationData(c.handleApplicationData)
}

func (c *Cloud) handleProflingMetrics(payload, topic string) {
	context := &localContext{}
	json.Unmarshal([]byte(payload), context)
	c.context = context
}

func (c *Cloud) isResourcesAvailable() bool {
	if c.context == nil {
		return false
	}

	if c.context.CPU < 40.0 && c.context.Memory < 75.0 {
		return true
	}

	return false
}

func (c *Cloud) handleOffloadingRequest(payload string, topic string) {
	if !c.state.IsEmpty() {
		// TODO: add response
		log.Println("cloud: unable to accept offload because state is not LOCAL")
		return
	}

	// if !c.isResourcesAvailable() {
	// 	c.publisher.PublishOffloadingAllowed(false)
	// 	return
	// }

	// Context: resources usage, CEP latency?
	c.publisher.PublishOffloadingAllowed(true)
	err := c.state.To("OFF_ALLOWED")
	if err != nil {
		log.Println(err.Error())
	}
}

func (c *Cloud) saveState(directory, payload string) error {
	err := ioutil.WriteFile(directory, []byte(payload), 0644)
	if err != nil {
		log.Println("cloud: failed to save state")
		return err
	}

	return nil
}

func (c *Cloud) handleOffloadingState(payload string, topic string) {
	if !c.state.IsAllowed() {
		// TODO: add response
		return
	}

	start := time.Now()
	err := c.saveState(stateDirectory, payload)
	if err != nil {
		return
	}

	err = c.flink.RunJob(stateDirectory, parallelism)
	if err != nil {
		log.Println("cloud: failed to run offloaded job: ", err)
		return
	}
	elapsed := time.Since(start)
	log.Printf("cloud: saveState + RunJob took %s", elapsed)

	c.publisher.PublishOffloadingStateConfirm()
	c.state.To("OFF_IN_PROGRESS")
}

func (c *Cloud) handleOffloadingStopReq(payload string, topic string) {
	if !c.state.IsInProgress() {
		log.Println("unabled to stop because there's no offload in progress")
		return
	}

	state, err := c.flink.GetState()
	if err != nil {
		log.Println("cloud: cannot get state")
	}

	c.flink.StopJob() // TODO: check potential for inconsistency
	c.publisher.PublishOffloadingStopConfirm(state)
	log.Println("cloud: offloading stop confirmed: sending state")
	c.state.To("LOCAL")
}

func (c *Cloud) SetApplication(topic, application string) {
	c.application = application
}

func (c *Cloud) handleApplicationData(payload, topic string) {
	if !c.state.IsInProgress() {
		log.Println("cloud: unabled to process data because there's no offload in progress")
		return
	}

	c.publisher.PublishLocalApplicationData(topic, payload)
}
