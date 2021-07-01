package flink

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os/exec"
)

type Job struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

type RunJobResponse struct {
	JobId string `json:"jobid"`
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

func (f *Flink) RunJob(savepointPath string) error {
	f.address.Path = "/jars/" + f.jarId + "/run?entry-class=main&savepointPath=" + savepointPath

	resp, err := http.Post(f.address.String(), "application/json", nil)
	if err != nil {
		return err
	}

	response := &RunJobResponse{}
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
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

func (f *Flink) StartStandaloneJob() error {
	_, err := exec.Command("serviceman", "start", "app-edge").Output()
	if err != nil {
		fmt.Println(err)
		return fmt.Errorf("error starting service: %w", err)
	}
	return nil
}

func (f *Flink) StopStandaloneJob() error {
	_, err := exec.Command("serviceman", "stop", "app-edge").Output()
	if err != nil {
		fmt.Println(err)
		return fmt.Errorf("error stopping service: %w", err)
	}
	return nil
}
