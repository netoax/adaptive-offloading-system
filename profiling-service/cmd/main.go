package main

import (
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/netoax/profiling-service/pkg/flink"
	"github.com/netoax/profiling-service/pkg/monitor"
	"github.com/netoax/profiling-service/pkg/mqtt"
	"github.com/netoax/profiling-service/pkg/system"
)

type configuration struct {
	jobID          string
	devicePolling  int
	flinkPolling   int
	flinkAddress   string
	networkPolling int
	iperfServer    bool
	iperfAddress   string
	cepEnabled     bool
	networkEnabled bool
}

func getConfig() configuration {
	config := configuration{"", 30, 60, "", 60, false, "", true, true}

	if os.Getenv("FLINK_JOB_ID") != "" {
		config.jobID = os.Getenv("FLINK_JOB_ID")
	}

	if os.Getenv("FLINK_SERVER_ADDRESS") != "" {
		config.flinkAddress = os.Getenv("FLINK_SERVER_ADDRESS")
	}

	if os.Getenv("DEVICE_METRICS_POLLING") != "" {
		config.devicePolling, _ = strconv.Atoi(os.Getenv("DEVICE_METRICS_POLLING"))
	}
	if os.Getenv("FLINK_METRICS_POLLING") != "" {
		config.flinkPolling, _ = strconv.Atoi(os.Getenv("FLINK_METRICS_POLLING"))
	}
	if os.Getenv("NETWORK_METRICS_POLLING") != "" {
		config.networkPolling, _ = strconv.Atoi(os.Getenv("NETWORK_METRICS_POLLING"))
	}
	if os.Getenv("IPERF_SERVER") != "" {
		config.iperfServer, _ = strconv.ParseBool(os.Getenv("IPERF_SERVER"))
	}
	if os.Getenv("IPERF_SERVER_ADDRESS") != "" {
		config.iperfAddress = os.Getenv("IPERF_SERVER_ADDRESS")
	}
	if os.Getenv("CEP_ENABLED") != "" {
		config.cepEnabled, _ = strconv.ParseBool(os.Getenv("CEP_ENABLED"))
	}
	if os.Getenv("NET_ENABLED") != "" {
		config.networkEnabled, _ = strconv.ParseBool(os.Getenv("NET_ENABLED"))
	}

	return config
}

func main() {
	config := getConfig()
	networkClientProf := system.NewNetworkProfilerClient(config.iperfAddress)
	deviceProfiler := system.DeviceProfiler{}
	broker := mqtt.NewBroker("tcp://localhost:1883", "test")
	broker.Start()

	if config.iperfServer {
		networkServerProf := system.NewNetworkProfilerServer()
		err := networkServerProf.Start()
		if err != nil {
			fmt.Println(err)
		}
	}

	publisher := mqtt.NewPublisher(*broker)
	subscriber := mqtt.NewSubscriber(*broker)
	flinkService := flink.NewProxy(config.flinkAddress, config.jobID)
	scheduler := monitor.NewMetricsScheduler(publisher, deviceProfiler, flinkService, &networkClientProf, config.networkEnabled, config.cepEnabled)
	log.Println("starting iperf...")

	subscriber.Subscribe("/profiling/job/id", flinkService.SetJobID)

	scheduler.SetPolling(config.devicePolling)
	if !config.iperfServer {
		err := networkClientProf.Start()
		if err != nil {
			fmt.Println(err)
		}
	}

	scheduler.Start()
}
