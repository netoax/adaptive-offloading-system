package runner

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"strconv"
	"time"

	"github.com/netoax/adaptive-offloading-system/decision/pkg/flink"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/mqtt"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/state"
)

const (
	startTimeout            = 5
	stopTimeout             = 5
	intervalBetweenOffloads = 10
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
	// dependencies
	subscriber *mqtt.MessageSubscriber
	publisher  *mqtt.MessagePublisher
	flink      *flink.Flink

	mlEnabled bool

	// values holder
	lastOffloadTime time.Time
	state           *state.State
	application     string
	jobRunning      chan bool
	fallback        bool
	violated        bool

	// content buffer
	buffer  []string
	timeout float64
}

type OffloadingSignal struct {
	Status bool `json:"status"`
}

func NewEdge(subscriber *mqtt.MessageSubscriber, publisher *mqtt.MessagePublisher, flink *flink.Flink, timeout float64, mlEnabled bool) *Edge {
	state := state.NewState("edge")
	return &Edge{subscriber, publisher, flink, mlEnabled, time.Time{}, state, "", make(chan bool), !mlEnabled, false, []string{}, timeout}
}

func (e *Edge) hasBuffer() bool { return len(e.buffer) != 0 }

func (e *Edge) Start() {
	// <-e.jobRunning
	e.SetupSubscriptions()
}

func (e *Edge) print() {
	currentTime := time.Now()
	oc := &OverallContext{
		State:      e.state.GetState(),
		Violated:   e.violated,
		Fallback:   e.fallback,
		BufferSize: len(e.buffer),
		Timestamp:  currentTime.Format("2006-01-02T15:04:05-0700"),
	}

	encodedResponse, _ := json.Marshal(oc)
	fmt.Println(string(encodedResponse))
}

func (e *Edge) SetupSubscriptions() {
	e.subscriber.OnOffloadingRequest(e.handleOffloadingSignal)

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

func (e *Edge) isModelHealth(context *PredictionContext) bool {
	return context.Accuracy > 0.95 && context.Precision > 0.95 && context.Recall > 0.8
}

func (e *Edge) isOffloadable(status bool) bool {
	if status && e.state.IsEmpty() {
		return true
	}

	return false
}

/*
* timeout, when?
* - increase when there's an offloading request, successfully offloading
* - what about adding in state machine level?
 */

func (e *Edge) handleOffloadingSignal(payload, topic string) {
	elapsed := time.Since(e.lastOffloadTime)
	if elapsed.Minutes() < e.timeout {
		return
	}
	// fmt.Println(elapsed.Minutes())
	status := e.updatePrediction(payload)
	isOffloadable := e.isOffloadable(status)
	e.print()
	if e.shouldStopOffloading(isOffloadable) {
		e.publisher.PublishOffloadingStop()
		e.updateTimeout()
		return
	}

	if e.state.IsInProgress() {
		e.updateTimeout()
		return
	}

	if e.shouldStartOffloading(isOffloadable) {
		e.publisher.PublishOffloadingRequest()
		e.state.To("OFF_REQ")
		e.updateTimeout()
	}
}

func (e *Edge) updatePrediction(payload string) bool {
	context := &PredictionContext{}
	json.Unmarshal([]byte(payload), context)
	e.fallback = !e.isModelHealth(context) // TODO: add concept drift
	// log.Printf("edge: fallback status is %t", e.fallback)
	return context.Status
}

func (e *Edge) shouldStopOffloading(status bool) bool {
	if !e.state.IsInProgress() {
		return false
	}

	if !e.fallback {
		return !status
	}

	if !e.violated {
		return true
	}

	return false
}

func (e *Edge) shouldStartOffloading(status bool) bool {
	if !e.state.IsEmpty() {
		return false
	}

	if !e.fallback {
		return status
	}

	if e.violated {
		return true
	}

	return false
}

func (e *Edge) updateTimeout() {
	e.lastOffloadTime = time.Now()
}

func (e *Edge) handlePolicyStatusUpdate(payload, topic string) {
	context := &PoliciesContext{}
	json.Unmarshal([]byte(payload), context)

	e.violated = context.Violated
	if !e.mlEnabled && context.Violated {
		e.tryOffloading(context.Violated)
	}

	// e.print()
	// log.Printf("edge: policy violation status update to %t", e.violated)
}

func (e *Edge) tryOffloading(status bool) {
	isOffloadable := e.isOffloadable(status)
	e.print()
	if e.shouldStopOffloading(isOffloadable) {
		e.publisher.PublishOffloadingStop()
		e.updateTimeout()
		return
	}

	if e.state.IsInProgress() {
		e.updateTimeout()
		return
	}

	if e.shouldStartOffloading(isOffloadable) {
		e.publisher.PublishOffloadingRequest()
		e.state.To("OFF_REQ")
		e.updateTimeout()
	}
}

func (e *Edge) handleConceptDrift(payload, topic string) {
	// context := &PoliciesContext{}
	// json.Unmarshal([]byte(payload), context)

	// e.policiesCtx = context
	log.Println("edge: concept drift alert received")
}

func (e *Edge) sendBuffer(topic string) {
	for _, payload := range e.buffer {
		e.publisher.PublishRemoteApplicationData(topic, payload)
		_, e.buffer = e.buffer[len(e.buffer)-1], e.buffer[:len(e.buffer)-1]
	}
}

func (e *Edge) accBuffer(payload string) {
	if e.state.IsAllowed() {
		e.buffer = append(e.buffer, payload)
	}
}

func (e *Edge) handleApplicationData(payload, topic string) {
	if e.state.IsInProgress() {
		// log.Println("edge: sending application data")
		e.publisher.PublishRemoteApplicationData(topic, payload)
	}

	if e.state.IsAllowed() {
		// log.Println("edge: adding data to buffer")
		e.accBuffer(payload)
		return
	}

	if e.hasBuffer() {
		e.print()
		// log.Printf("edge: sending %d objects from buffer", len(e.buffer))
		e.sendBuffer(topic)
	}

	e.publisher.PublishLocalApplicationData(topic, payload)
}

func (e *Edge) handleOffloadingAllowed(payload, topic string) {
	allowed, _ := strconv.ParseBool(payload)
	if !allowed {
		e.state.To("LOCAL")
		e.print()
		// log.Printf("edge: offloading not allowed")
		return
	}

	err := e.state.To("OFF_ALLOWED")
	if err != nil {
		log.Printf(err.Error())
		return
	}

	// start := time.Now()
	state, _ := e.flink.GetState()
	// elapsed := time.Since(start)

	// log.Printf("edge: get state took %s", elapsed)

	e.publisher.PublishOffloadingState(state)
	e.print()
	// log.Println("edge: state sent to the cloud")
}

func (e *Edge) handleStateConfirmed(payload, topic string) {
	e.state.To("OFF_IN_PROGRESS")
	// start := time.Now()
	e.flink.StopStandaloneJob(e.application)
	// elapsed := time.Since(start)
	// log.Printf("edge: stop job took %s", elapsed)
}

func (e *Edge) handleStopConfirmed(payload, topic string) {
	err := ioutil.WriteFile("/tmp/state", []byte(payload), 0644)
	if err != nil {
		log.Println("edge: failed to write state file")
		return
	}

	// log.Println("edge: state written, starting again")
	e.print()
	jobId, _ := e.flink.StartStandaloneJob(e.application) // TODO: move this to before confirmation?
	e.publisher.PublishJobID(jobId)
	e.state.To("LOCAL")
}

func (e *Edge) SetApplication(application, topic string) {
	jobId, _ := e.flink.StartStandaloneJob(application)
	e.publisher.PublishJobID(jobId)

	e.jobRunning <- true
	e.application = application
}
