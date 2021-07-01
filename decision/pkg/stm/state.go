package stm

import (
	"fmt"

	"github.com/looplab/fsm"
)

type Offloading struct {
	FSM *fsm.FSM
}

var (
	ST_OFFLOADING_REQUEST = "OFF_REQ"
	ST_OFFLOADING_OK      = "OFF_OK"
)

var (
	EV_OFFLOADING_SIGNAL = "signal"
)

func NewOffloading() *Offloading {
	offloading := &Offloading{}

	offloading.FSM = fsm.NewFSM(
		"empty",
		fsm.Events{
			{Name: "clear", Src: []string{"ready"}, Dst: "empty"},
			{Name: EV_OFFLOADING_SIGNAL, Src: []string{"empty"}, Dst: ST_OFFLOADING_REQUEST},
			// {Name: "off_req", Src: []string{"empty"}, Dst: "OFF_REQ"},
			// {Name: "off_ack", Src: []string{"empty"}, Dst: "OFF_OK"},
			// {Name: "off_stop", Src: []string{"empty"}, Dst: "STOP_REQ"},
			// {Name: "off_ok", Src: []string{"empty"}, Dst: "STOP_OK"},
		},
		fsm.Callbacks{
			EV_OFFLOADING_SIGNAL: func(e *fsm.Event) { offloading.init(e) },
			// "enter_OFF_REQ": func(e *fsm.Event) { offloading.request(e) },
		},
	)

	return offloading
}

func (o *Offloading) init(e *fsm.Event) {
	fmt.Println("Requesting offloading permission to remote node")
}

func (o *Offloading) request(e *fsm.Event) {
	fmt.Println("Requesting offloading permission to remote node")
}
