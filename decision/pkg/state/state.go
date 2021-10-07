package state

import (
	"encoding/json"
	"fmt"
	"log"
	"time"
)

var edgeStates = map[string]string{
	"LOCAL":           "OFF_REQ",
	"OFF_REQ":         "OFF_ALLOWED",
	"OFF_ALLOWED":     "OFF_IN_PROGRESS",
	"OFF_IN_PROGRESS": "LOCAL",
}

var cloudStates = map[string]string{
	"LOCAL":           "OFF_ALLOWED",
	"OFF_ALLOWED":     "OFF_IN_PROGRESS",
	"OFF_IN_PROGRESS": "LOCAL",
}

type State struct {
	mode        string
	transitions map[string]string
	state       string
}

func NewState(mode string) *State {
	var state *State

	switch mode {
	case "edge":
		state = &State{mode, edgeStates, "LOCAL"}
		break
	case "cloud":
		state = &State{mode, cloudStates, "LOCAL"}
		break
	default:
		log.Println("unsupported mode: ", mode)
		return nil
	}

	return state
}
func (s *State) printTransition(actual, to string) {
	currentTime := time.Now()
	resp := map[string]interface{}{
		"timestamp": currentTime.Format("2006-01-02T15:04:05-0700"),
		"type":      "state-transition",
		"actual":    actual,
		"to":        to,
	}

	encodedResponse, _ := json.Marshal(resp)
	fmt.Println(string(encodedResponse))
}

func (s *State) To(state string) error {
	allowed := s.transitions[s.state]
	if allowed != state && state != "LOCAL" {
		// log.Printf("%s: unable to transit from %s to %s", s.mode, s.state, state)
		return fmt.Errorf("%s: unable to transit from %s to %s", s.mode, s.state, state)
	}

	// log.Printf("%s: state update: %s -> %s", s.mode, s.state, state)
	s.printTransition(s.state, state)

	s.state = state
	return nil
}

func (s *State) IsAllowed() bool { return s.state == "OFF_ALLOWED" }

func (s *State) IsInProgress() bool { return s.state == "OFF_IN_PROGRESS" }

func (s *State) IsEmpty() bool { return s.state == "LOCAL" }

func (s *State) GetState() string { return s.state }
