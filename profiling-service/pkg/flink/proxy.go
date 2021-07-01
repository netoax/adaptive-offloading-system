package flink

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"strings"
)

// FlinkService ...
type FlinkService interface {
	GetMetrics() (*FinalResponse, error)
	GetJobs() ([]*FlinkJob, error)
	// CancelAllJobs() error
}

// Proxy ...
type Proxy struct {
	address *url.URL
	jobID   string
}

// NewProxy ...
func NewProxy(address string, jobID string) *Proxy {
	url, err := url.Parse(fmt.Sprintf("http://%s", address))
	if err != nil {
		fmt.Println("cannot parse URL")
	}

	return &Proxy{url, jobID}
}

const (
	// NumRecordsInPerSecond ...
	NumRecordsInPerSecond = "0.numRecordsInPerSecond"

	// NumRecordsOutPerSecond ...
	NumRecordsOutPerSecond = "0.numRecordsOutPerSecond"

	// IsBackPressured ...
	IsBackPressured = "0.isBackPressured"
)

var verticeMetrics = []string{
	NumRecordsInPerSecond,
	NumRecordsOutPerSecond,
	IsBackPressured,
}

// FlinkJob ...
type FlinkJob struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

type flinkRequest struct {
	Path          string
	Method        string
	Body          interface{}
	Authorization string
}

// VerticeFlink ...
type VerticeFlink struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

// VerticeResponse ...
type VerticeResponse struct {
	ID      string                 `json:"id"`
	Name    string                 `json:"name"`
	Metrics map[string]interface{} `json:"metrics"`
}

// FinalResponse ...
type FinalResponse struct {
	Vertices []*VerticeResponse     `json:"vertice"`
	Metrics  map[string]interface{} `json:"metrics"`
	// LatencyMetrics []*MetricResponse `json:"latencyMetrics,omitempty"`
}

// Job ...
type Job struct {
	Vertices []*VerticeFlink `json:"vertices"`
}

// MetricResponse ...
type MetricResponse struct {
	ID    string `json:"id"`
	Value string `json:"value"`
}

func (p *Proxy) SetJobID(id string) {
	log.Printf("changing job from %s to %s", p.jobID, id)
	p.jobID = id
}

func (p *Proxy) buildVerticeMetricsQuery(verticeID string, params ...string) string {
	q := p.address.Query()
	q.Set("get", strings.Join(params, ","))
	p.address.Path = "/jobs/" + p.jobID + "/vertices/" + verticeID + "/metrics"
	p.address.RawQuery = q.Encode()
	return p.address.String()
}

// ListVertices ...
func (p *Proxy) ListVertices() ([]*VerticeFlink, error) {
	p.address.Path = "/jobs/" + p.jobID
	resp, err := http.Get(p.address.String())
	if err != nil {
		return nil, err
	}

	var response *Job
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}
	defer resp.Body.Close()

	return response.Vertices, nil
}

// Get ...
func (p *Proxy) GetMetrics() (*FinalResponse, error) {
	vertices, err := p.ListVertices()
	if err != nil {
		return nil, err
	}

	vResp := []*VerticeResponse{}

	for _, v := range vertices {
		metrics, err := p.GetVerticeMetrics(v.ID)
		if err != nil {
			return nil, err
		}

		var metricsObj map[string]interface{}
		metricsObj = make(map[string]interface{})
		for _, m := range metrics {
			metricsObj[m.ID] = m.Value
		}

		vResp = append(vResp, &VerticeResponse{v.ID, v.Name, metricsObj})
	}

	if len(vResp) < 2 {
		return nil, errors.New("not enough operators to track latency")
	}

	// fmt.Println(vResp[0].ID, vResp[len(vResp)-1].ID)
	latency, err := p.GetLatencyBetweenOperators(99, vResp[0].ID, vResp[len(vResp)-1].ID)
	if err != nil {
		return nil, err
	}

	var generalMetrics map[string]interface{}
	generalMetrics = make(map[string]interface{})
	// fmt.Println(latency)

	// generalMetrics["latency"] = 0

	if len(latency) > 0 {
		generalMetrics["latency"] = latency[0].Value
	} else {
		generalMetrics["latency"] = 0
	}

	return &FinalResponse{vResp, generalMetrics}, nil
}

// GetVerticeMetrics ...
func (p *Proxy) GetVerticeMetrics(id string) ([]*MetricResponse, error) {
	address := p.buildVerticeMetricsQuery(id, verticeMetrics...)
	resp, err := http.Get(address)
	if err != nil {
		return nil, err
	}

	var response []*MetricResponse
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()

	return response, nil
}

func (p *Proxy) buildLatencyMetricsQuery(percentil int, operator1, operator2 string) string {
	q := p.address.Query()
	param := fmt.Sprintf("latency.source_id.%s.operator_id.%s.operator_subtask_index.0.latency_p%d", operator1, operator2, percentil)
	q.Set("get", param)
	p.address.Path = "/jobs/" + p.jobID + "/metrics"
	p.address.RawQuery = q.Encode()
	return p.address.String()
}

// GetLatencyBetweenOperators ...
func (p *Proxy) GetLatencyBetweenOperators(percentil int, operator1, operator2 string) ([]*MetricResponse, error) {
	address := p.buildLatencyMetricsQuery(percentil, operator1, operator2)
	resp, err := http.Get(address)
	if err != nil {
		return nil, err
	}

	var response []*MetricResponse
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()

	return response, nil
}

// GetAllJobs ...
func (p *Proxy) GetJobs() ([]*FlinkJob, error) {
	p.address.Path = "/jobs"
	resp, err := http.Get(p.address.String())
	if err != nil {
		return nil, err
	}

	var response map[string][]*FlinkJob
	decoder := json.NewDecoder(resp.Body)
	err = decoder.Decode(&response)
	if err != nil {
		return nil, fmt.Errorf("error decoding response: %w", err)
	}

	defer resp.Body.Close()
	return response["jobs"], nil
}

// // CancelAllJobs ...
// func (p *Proxy) CancelAllJobs() error {
// 	jobs, err := p.GetJobs()
// 	if err != nil {
// 		return err
// 	}

// 	for _, j := range jobs {
// 		err = p.CancelJob(j.ID)
// 		if err != nil {
// 			return err
// 		}
// 	}

// 	return nil
// }

// // CancelJob ...
// func (p *Proxy) CancelJob(id string) error {
// 	p.address.Path = "/jobs/" + id + "/yarn-cancel"
// 	resp, err := http.Get(p.address.String())
// 	if err != nil {
// 		return nil, err
// 	}

// 	return err
// }
