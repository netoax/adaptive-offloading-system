package monitor

import (
	"encoding/json"
	"log"
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
	s.scheduler.Every(time).Seconds().Do(s.sendMetrics)
}

func (s *Scheduler) sendMetrics() error {
	cpu, err := s.deviceProfiler.GetCPU()
	if err != nil {
		log.Println(err)
		return err
	}

	mem, err := s.deviceProfiler.GetMemory()
	if err != nil {
		log.Println(err)
		return err
	}

	resp := map[string]interface{}{
		"cpu":    cpu[0],
		"memory": mem,
	}

	if s.netEnabled {
		bandwidth, err := s.netProfiler.GetBandwidthMbps()
		if err != nil {
			log.Println(err)
			return err
		}

		rtt, err := s.netProfiler.GetAverageRtt()
		if err != nil {
			log.Println(err)
			return err
		}

		resp["bandwidth"] = bandwidth
		resp["rtt"] = rtt
	}

	if s.cepEnabled {
		response, err := s.flink.GetMetrics()
		if err != nil {
			log.Println(err)
		} else {
			resp["cepLatency"] = response.Metrics["latency"]
		}
	}

	encodedResponse, err := json.Marshal(resp)
	if err != nil {
		return err
	}

	// prettyResponse, err := json.MarshalIndent(resp, "", " ")
	// if err != nil {
	// 	return err
	// }

	log.Println(resp)
	s.publisher.Publish("/profiling/metrics", encodedResponse)

	return nil
}
