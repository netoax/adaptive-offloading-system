package flink

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"time"
)

const savepointIntervalInSeconds = 15

type SavepointRequest struct {
	TargetDirectory string `json:"target-directory"`
	CancelJob       bool   `json:"cancel-job"`
}

type SavepointResponse struct {
	RequestID string `json:"request-id"`
}

type SavepointStatus struct {
	ID string `json:"id"`
}

type SavepointOperation struct {
	Location string `json:"location"`
}

type SavepointInfo struct {
	Status    *SavepointStatus    `json:"status"`
	Operation *SavepointOperation `json:"operation"`
}

func (f *Flink) GetState() ([]byte, error) {
	jobs, err := f.GetJobs()
	if err != nil {
		log.Println("cannot list Flink jobs")
		return nil, err
	}

	jobId := jobs[0].ID
	f.jobId = jobId

	triggerId, err := f.TriggerSavepoint(jobId)
	if err != nil {
		return nil, err
	}

	location, err := f.GetLocation(jobId, triggerId)
	if err != nil {
		return nil, err
	}

	content, err := ioutil.ReadFile(strings.ReplaceAll(location, "file:", "") + "/_metadata")
	if err != nil {
		return nil, err
	}

	return content, nil
}

func (f *Flink) TriggerSavepoint(jobId string) (string, error) {
	f.address.Path = "/jobs/" + jobId + "/savepoints"

	req := &SavepointRequest{"file:///tmp/savepoints", false}
	jsonReq, err := json.Marshal(req)
	if err != nil {
		return ",", err
	}

	responseBody := bytes.NewBuffer(jsonReq)

	resp, err := http.Post(f.address.String(), "application/json", responseBody)
	if err != nil {
		return "", err
	}

	response := &SavepointResponse{}

	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(response)
	if err != nil {
		return "", err
	}

	return response.RequestID, nil
}

func (f *Flink) GetLocation(jobId, triggerId string) (string, error) {
	ticker := time.NewTicker(1 * time.Second)
	var location string
	status := make(chan bool)
	go func() {
		for range ticker.C {
			savepoint, err := f.getSavepoint(jobId, triggerId) // TODO: find more lightweight operation
			if err != nil {
				continue
			}

			// fmt.Println(triggerId)
			if savepoint.Operation == nil {
				continue
			}

			// fmt.Println(savepoint.Operation)

			location = savepoint.Operation.Location
			status <- true
		}
	}()

	<-status
	// fmt.Println(location)
	return location, nil
}

func (f *Flink) getSavepoint(jobId, triggerId string) (*SavepointInfo, error) {
	f.address.Path = "/jobs/" + jobId + "/savepoints/" + triggerId
	resp, err := http.Get(f.address.String())
	if err != nil {
		return nil, err
	}

	response := &SavepointInfo{}
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()
	return response, nil
}

func (f *Flink) RestoreSavepoint() error {

	return nil
}
