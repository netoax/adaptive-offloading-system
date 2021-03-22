package main

import (
	"github.com/netoax/profiling-service/pkg/flink"
	"github.com/netoax/profiling-service/pkg/monitor"
	"github.com/netoax/profiling-service/pkg/mqtt"
	"github.com/netoax/profiling-service/pkg/system"
)

func main() {
	deviceProfiler := system.DeviceProfiler{}

	broker := mqtt.NewBroker("tcp://localhost:1883", "test")
	broker.Start()

	publisher := mqtt.NewPublisher(*broker)

	flinkService := flink.NewProxy("localhost", 8081, "0ad78fc6b382a4e53869281545cdff6c")

	scheduler := monitor.NewMetricsScheduler(publisher, deviceProfiler, flinkService)

	scheduler.SetDevicePolling(5)
	scheduler.SetFlinkPolling(5)
	scheduler.Start()
}
