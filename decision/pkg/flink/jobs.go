package flink

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
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
	parameters := url.Values{}
	parameters.Add("entry-class", "main")
	parameters.Add("savepointPath", savepointPath)
	parameters.Add("parallelism", parallelism)
	f.address.RawQuery = parameters.Encode()
	f.address.Path = "/jars/" + f.jarId + "/run"
	fmt.Println(f.address.String())
	resp, err := http.Post(f.address.String(), "application/json", nil)
	if err != nil {
		return err
	}

	fmt.Println(resp)

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

func (f *Flink) StartStandaloneJob(name string) (string, error) {
	_, err := exec.Command("/bin/sh", "-c", "sudo systemctl start "+name).Output()
	if err != nil {
		fmt.Println(err)
		return "", fmt.Errorf("error starting service: %w", err)
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
		fmt.Println(err)
		return fmt.Errorf("error stopping service: %w", err)
	}

	return nil
}
