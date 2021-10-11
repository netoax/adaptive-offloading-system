package flink

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os/exec"
	"time"
)

type Job struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

type RunJobResponse struct {
	JobId string `json:"jobid"`
}

type RunJobInformation struct {
	EntryClass    string `json:"entryClass"`
	Parallelism   string `json:"parallelism"`
	ProgramArgs   string `json:"programArgs"`
	SavepointPath string `json:"savepointPath"`
}

func (f *Flink) GetJobs() ([]*Job, error) {
	f.address.Path = "/jobs"
	resp, err := http.Get(f.address.String())
	if err != nil {
		return nil, err
	}

	var response map[string][]*Job
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()
	return response["jobs"], nil
}

func (f *Flink) RunJob(savepointPath, parallelism string) error {
	info := &RunJobInformation{
		EntryClass:    "main",
		Parallelism:   parallelism,
		ProgramArgs:   "--mode cloud",
		SavepointPath: savepointPath,
	}

	body, err := json.Marshal(info)
	if err != nil {
		return err
	}

	f.address.Path = "/jars/" + f.jarId + "/run"
	resp, err := http.Post(f.address.String(), "application/json", bytes.NewBuffer(body))
	if err != nil {
		return err
	}

	if resp.StatusCode != 200 {
		return errors.New("fail to make http request")
	}

	return f.updateJobID(resp)
}

func (f *Flink) updateJobID(resp *http.Response) error {
	response := &RunJobResponse{}
	decoder := json.NewDecoder(resp.Body)
	err := decoder.Decode(&response)
	if err != nil {
		return fmt.Errorf("error decoding response: %w", err)
	}

	f.jobId = response.JobId
	return nil
}

func (f *Flink) StopJob() error {
	f.address.Path = "/jobs/" + f.jobId
	req, _ := http.NewRequest("PATCH", f.address.String(), nil)
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return nil
}

func (f *Flink) StartStandaloneJob(name string) (string, error) {
	_, err := exec.Command("/bin/sh", "-c", "sudo systemctl start "+name).Output()
	if err != nil {
		return "", fmt.Errorf("error starting %s service: %w", name, err)
	}

	var jobs []*Job

	ticker := time.NewTicker(1 * time.Second)
	status := make(chan bool)
	go func() {
		for range ticker.C {
			jobs, err = f.GetJobs() // TODO: find more lightweight operation
			if err != nil {
				continue
			}

			status <- true
		}
	}()

	<-status
	ticker.Stop()
	return jobs[0].ID, nil
}

func (f *Flink) StopStandaloneJob(name string) error {
	_, err := exec.Command("/bin/sh", "-c", "sudo systemctl stop "+name).Output()
	if err != nil {
		return fmt.Errorf("error stopping %s service: %w", name, err)
	}

	return nil
}
