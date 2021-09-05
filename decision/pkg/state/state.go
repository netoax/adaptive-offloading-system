package state

import "log"

var edgeStates = map[string]string{
	"EMPTY":           "OFF_REQ",
	"OFF_REQ":         "OFF_ALLOWED",
	"OFF_ALLOWED":     "OFF_IN_PROGRESS",
	"OFF_IN_PROGRESS": "EMPTY",
}

var cloudStates = map[string]string{
	"EMPTY":           "OFF_ALLOWED",
	"OFF_ALLOWED":     "OFF_IN_PROGRESS",
	"OFF_IN_PROGRESS": "EMPTY",
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
		state = &State{mode, edgeStates, "EMPTY"}
		break
	case "cloud":
		state = &State{mode, cloudStates, "EMPTY"}
		break
	default:
		log.Println("unsupported mode: ", mode)
		return nil
	}

	return state
}

func (s *State) To(state string) {
	allowed := s.transitions[s.state]
	if allowed != state {
		log.Printf("%s: unable to transit from %s to %s", s.mode, s.state, state)
		return
	}

	log.Printf("%s: state update: %s -> %s", s.mode, s.state, state)
	s.state = state
}

func (s *State) IsAllowed() bool { return s.state == "OFF_ALLOWED" }

func (s *State) IsInProgress() bool { return s.state == "OFF_IN_PROGRESS" }

func (s *State) IsEmpty() bool { return s.state == "EMPTY" }

func (s *State) GetState() string { return s.state }
