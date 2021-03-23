package main

import (
	"os"
	"strconv"

	"github.com/netoax/profiling-service/pkg/flink"
	"github.com/netoax/profiling-service/pkg/monitor"
	"github.com/netoax/profiling-service/pkg/mqtt"
	"github.com/netoax/profiling-service/pkg/system"
)

type configuration struct {
	jobID         string
	devicePolling int
	flinkPolling  int
}

func getConfig() configuration {
	config := configuration{"", 5, 5}

	if os.Getenv("FLINK_JOB_ID") != "" {
		config.jobID = os.Getenv("FLINK_JOB_ID")
	}

	if os.Getenv("DEVICE_METRICS_POLLING") != "" {
		config.devicePolling, _ = strconv.Atoi(os.Getenv("DEVICE_METRICS_POLLING"))
	}
	if os.Getenv("FLINK_METRICS_POLLING") != "" {
		config.flinkPolling, _ = strconv.Atoi(os.Getenv("FLINK_METRICS_POLLING"))
	}

	return config
}

func main() {
	deviceProfiler := system.DeviceProfiler{}
	config := getConfig()
	broker := mqtt.NewBroker("tcp://localhost:1883", "test")
	broker.Start()

	publisher := mqtt.NewPublisher(*broker)
	subscriber := mqtt.NewSubscriber(*broker)
	flinkService := flink.NewProxy("localhost", 8081, config.jobID)
	scheduler := monitor.NewMetricsScheduler(publisher, deviceProfiler, flinkService)

	subscriber.Subscribe("/profiling/job/id", flinkService.SetJobID)

	scheduler.SetDevicePolling(config.devicePolling)
	scheduler.SetFlinkPolling(config.flinkPolling)
	scheduler.Start()
}
