package monitor

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/go-co-op/gocron"
	"github.com/netoax/profiling-service/pkg/flink"
	"github.com/netoax/profiling-service/pkg/mqtt"
	"github.com/netoax/profiling-service/pkg/system"
)

// MetricsScheduler ...
type MetricsScheduler interface {
	SetDevicePolling()
	SetFlinkPolling()
	SetNetworkPolling()
}

// Scheduler ...
type Scheduler struct {
	scheduler      *gocron.Scheduler
	publisher      mqtt.Publisher
	deviceProfiler system.DeviceProfiler
	flink          flink.FlinkService
	netProfiler    *system.NetworkProfClient
	netEnabled     bool
	cepEnabled     bool
}

// NewMetricsScheduler ...
func NewMetricsScheduler(
	publisher mqtt.Publisher,
	deviceProfiler system.DeviceProfiler,
	flink flink.FlinkService,
	netProfiler *system.NetworkProfClient,
	netEnabled bool,
	cepEnabled bool,
) *Scheduler {
	scheduler := gocron.NewScheduler(time.UTC)
	return &Scheduler{scheduler, publisher, deviceProfiler, flink, netProfiler, netEnabled, cepEnabled}
}

// Start ...
func (s *Scheduler) Start() {
	s.scheduler.StartBlocking()
}

// SetDevicePolling ...
func (s *Scheduler) SetPolling(time int) {
	os.Setenv("BR", "America/Fortaleza")
	s.scheduler.Every(time).Seconds().Do(s.sendMetrics)
}

func (s *Scheduler) sendMetrics() error {
	cpu, err := s.deviceProfiler.GetCPU()
	if err != nil {
		cpu = []float64{0.0}
	}

	mem, err := s.deviceProfiler.GetMemory()
	if err != nil {
		mem = 0.0
	}

	currentTime := time.Now()
	resp := map[string]interface{}{
		"timestamp": currentTime.Format("2006-01-02T15:04:05-0700"),
		"cpu":       cpu[0],
		"memory":    mem,
	}

	if s.netEnabled {
		bandwidth, err := s.netProfiler.GetBandwidthMbps()
		if err != nil {
			return err
		}

		rtt, err := s.netProfiler.GetAverageRtt()
		if err != nil {
			return err
		}

		resp["bandwidth"] = bandwidth
		resp["rtt"] = rtt
	}

	if s.cepEnabled {
		response, err := s.flink.GetMetrics()
		if err != nil {
			resp["cepLatency"] = 0.0
		} else {
			resp["cepLatency"] = response.Metrics["latency"]
		}
	}

	encodedResponse, err := json.Marshal(resp)
	if err != nil {
		return err
	}

	fmt.Println(string(encodedResponse))
	s.publisher.Publish("/profiling/metrics", encodedResponse)

	return nil
}
