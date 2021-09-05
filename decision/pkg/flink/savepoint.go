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

// type Savepointer interface {
// 	Save() error
// 	GetLocation() error
// }

const savepointIntervalInSeconds = 5

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
	Status    SavepointStatus    `json:"status"`
	Operation SavepointOperation `json:"operation"`
}

func (f *Flink) GetState() ([]byte, error) {
	jobs, err := f.GetJobs()
	if err != nil {
		log.Println("cannot list Flink jobs")
	}

	jobId := jobs[0].ID
	f.jobId = jobId // TODO: ss

	triggerId, err := f.TriggerSavepoint(jobId)
	if err != nil {
		return nil, err
	}

	time.Sleep(savepointIntervalInSeconds * time.Second)

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
	f.address.Path = "/jobs/" + jobId + "/savepoints/" + triggerId
	resp, err := http.Get(f.address.String())
	if err != nil {
		return "", err
	}

	response := &SavepointInfo{}
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return "", fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()
	return response.Operation.Location, nil
}

func (f *Flink) RestoreSavepoint() error {

	return nil
}
