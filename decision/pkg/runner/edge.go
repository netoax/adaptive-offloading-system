package runner

import (
	"encoding/json"
	"log"
	"time"

	"github.com/netoax/adaptive-offloading-system/decision/pkg/flink"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/mqtt"
)

type PredictionContext struct {
	Accuracy  float64 `json:"accuracy"`
	Precision float64 `json:"precision"`
	Recall    float64 `json:"recall"`
	Status    bool    `json:"status"`
}

type PoliciesContext struct {
	Violated bool `json:"violated"`
}

type Edge struct {
	subscriber      *mqtt.MessageSubscriber
	publisher       *mqtt.MessagePublisher
	flink           *flink.Flink
	predictionCtx   *PredictionContext
	policiesCtx     *PoliciesContext
	lastOffloadTime time.Time
	state           string
}

type OffloadingSignal struct {
	Status bool `json:"status"`
}

func NewEdge(subscriber *mqtt.MessageSubscriber, publisher *mqtt.MessagePublisher, flink *flink.Flink) *Edge {
	return &Edge{subscriber, publisher, flink, nil, nil, time.Time{}, "EMPTY"}
}

func (e *Edge) Start() {
	// offloading control
	e.subscriber.OnOffloadingSignal(e.handleOffloadingSignal)
	e.subscriber.OnOffloadingAllowed(e.handleOffloadingAllowed)
	e.subscriber.OnOffloadingStateConfirmed(e.handleStateConfirmed)
	e.subscriber.OnOffloadingStopConfirmed(e.handleStopConfirmed)

	// contextual data
	e.subscriber.OnPolicyStatusUpdate(e.handlePolicyStatusUpdate)
	e.subscriber.OnConceptDrift(e.handleConceptDrift)

	// incoming workload data
	e.subscriber.OnApplicationData(e.handleApplicationData)
}

func (e *Edge) isOffloadable(context *PredictionContext) bool {
	isModelHealthy := context.Accuracy > 0.95 || context.Precision > 0.95 || context.Recall > 0.8
	if context.Status && isModelHealthy && e.state == "EMPTY" {
		return true
	}

	return false
}

func (e *Edge) handleOffloadingSignal(payload, topic string) {
	log.Println("edge: offloading signal received")
	context := &PredictionContext{}
	json.Unmarshal([]byte(payload), context)
	log.Println("edge: context: ", context)

	elapsed := time.Since(e.lastOffloadTime)
	log.Println("edge: time since last offloading in seconds: ", elapsed.Minutes())
	if elapsed.Minutes() < 0.3 {
		return
	}

	if e.isOffloadable(context) {
		e.publisher.PublishOffloadingRequest()
		e.lastOffloadTime = time.Now()
		e.state = "OFF_REQ"
		return
	}

	// TBD: improve the stop handling
	if e.state == "OFF_IN_PROGRESS" {
		log.Println("edge: stopping")
		e.publisher.PublishOffloadingStop()
		e.lastOffloadTime = time.Now()
	}

	return
}

func (e *Edge) handlePolicyStatusUpdate(payload, topic string) {
	context := &PoliciesContext{}
	json.Unmarshal([]byte(payload), context)

	e.policiesCtx = context
	log.Println("edge: policies context updated")
}

func (e *Edge) handleConceptDrift(payload, topic string) {
	// context := &PoliciesContext{}
	// json.Unmarshal([]byte(payload), context)

	// e.policiesCtx = context
	log.Println("edge: concept drift alert received")
}

func (e *Edge) handleApplicationData(payload, topic string) {
	if e.state == "OFF_IN_PROGRESS" {
		e.publisher.PublishRemoteApplicationData(topic, payload)
		log.Println("edge: application data received: processing remote")
	} else if e.state == "EMPTY" {
		e.publisher.PublishLocalApplicationData(topic, payload)
		log.Println("edge: application data received: processing locally")
	}
}

func (e *Edge) handleOffloadingAllowed(payload, topic string) {
	log.Println("edge: offloading request allowed")

	if e.state != "OFF_REQ" {
		log.Println("edge: skipping offloading confirmation")
		return
	}

	state, _ := e.flink.GetState()
	e.publisher.PublishOffloadingState(state)

	e.state = "OFF_ALLOWED"
	log.Println("edge: state sent to the cloud")
}

func (e *Edge) handleStateConfirmed(payload, topic string) {
	log.Println("edge: offloading state confirmed")

	if e.state != "OFF_ALLOWED" {
		log.Println("edge: skipping state confirmation")
		return
	}

	e.flink.StopStandaloneJob()
	e.state = "OFF_IN_PROGRESS"
	// Ouvir evento de offloading started antes de atualizar esse estado
}

func (e *Edge) handleStopConfirmed(payload, topic string) {
	log.Println("edge: offloading stop confirmed")

	if e.state != "OFF_IN_PROGRESS" {
		log.Println("edge: skipping stop confirmation")
		return
	}

	log.Println("edge: starting again")
	e.state = "EMPTY"
	e.flink.StartStandaloneJob()
}
