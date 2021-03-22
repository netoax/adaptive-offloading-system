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
	flinkProfiler  flink.MetricsGetter
}

// NewMetricsScheduler ...
func NewMetricsScheduler(publisher mqtt.Publisher, deviceProfiler system.DeviceProfiler, flinkProfiler flink.MetricsGetter) *Scheduler {
	scheduler := gocron.NewScheduler(time.UTC)
	return &Scheduler{scheduler, publisher, deviceProfiler, flinkProfiler}
}

// Start ...
func (s *Scheduler) Start() {
	s.scheduler.StartBlocking()
}

// SetDevicePolling ...
func (s *Scheduler) SetDevicePolling(time int) {
	s.scheduler.Every(time).Seconds().Do(s.sendDeviceMetrics)
}

// SetFlinkPolling ...
func (s *Scheduler) SetFlinkPolling(time int) {
	s.scheduler.Every(time).Seconds().Do(s.sendFlinkMetrics)
}

// SetNetworkPolling ...
func (s *Scheduler) SetNetworkPolling(time int, params ...interface{}) {
	s.scheduler.Every(time).Seconds().Do(s.publisher.Publish, params)
}

func (s *Scheduler) sendDeviceMetrics() error {
	cpu, err := s.deviceProfiler.GetCPU()
	if err != nil {
		return err
	}

	mem, err := s.deviceProfiler.GetMemory()
	if err != nil {
		return err
	}

	response := map[string]interface{}{
		"cpu":    cpu[0],
		"memory": mem,
	}
	encodedResponse, err := json.Marshal(response)
	if err != nil {
		return err
	}

	log.Printf("device metrics obtained: publishing to MQTT broker: %s", encodedResponse)
	s.publisher.Publish("/metrics/device", encodedResponse)

	return nil
}

func (s *Scheduler) sendFlinkMetrics() error {
	response, err := s.flinkProfiler.Get()
	if err != nil {
		log.Println(err)
		return err
	}

	encodedResponse, err := json.Marshal(response)
	if err != nil {
		return err
	}

	log.Printf("CEP metrics obtained: publishing to MQTT broker: %s", encodedResponse)
	s.publisher.Publish("/metrics/cep", encodedResponse)

	return nil
}
