package main

import (
	"log"
	"os"
	"strconv"

	"github.com/netoax/adaptive-offloading-system/decision/pkg/flink"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/mqtt"
	"github.com/netoax/adaptive-offloading-system/decision/pkg/runner"
)

type config struct {
	executionMode     string
	localAddress      string
	remoteAddress     string
	flinkAddress      string
	jarId             string
	standaloneJarPath string
	app               string
	timeout           float64
	mlEnabled         bool
}

func getConfig() config {
	config := config{"edge", "tcp://localhost:1883", "tcp://localhost:1883", "http://localhost:8081", "", "", "", 2.0, false}

	if os.Getenv("EXECUTION_MODE") != "" {
		config.executionMode = os.Getenv("EXECUTION_MODE")
	}

	if os.Getenv("FLINK_ADDRESS") != "" {
		config.flinkAddress = os.Getenv("FLINK_ADDRESS")
	}

	if os.Getenv("FLINK_JAR_ID") != "" {
		config.jarId = os.Getenv("FLINK_JAR_ID")
	}

	if os.Getenv("FLINK_STANDALONE_JAR_PATH") != "" {
		config.standaloneJarPath = os.Getenv("FLINK_STANDALONE_JAR_PATH")
	}

	if os.Getenv("LOCAL_ADDRESS") != "" {
		config.localAddress = os.Getenv("LOCAL_ADDRESS")
	}

	if os.Getenv("REMOTE_ADDRESS") != "" {
		config.remoteAddress = os.Getenv("REMOTE_ADDRESS")
	}

	if os.Getenv("OFFLOADING_TIMEOUT") != "" {
		value, _ := strconv.ParseFloat(os.Getenv("OFFLOADING_TIMEOUT"), 64)
		config.timeout = value
	}

	if os.Getenv("ML_ENABLED") != "" {
		value, _ := strconv.ParseBool(os.Getenv("ML_ENABLED"))
		config.mlEnabled = value
	}

	return config
}

func main() {
	// fmt.Println("Hello World")
	config := getConfig()

	localConnection := mqtt.NewBroker(config.localAddress)
	remoteConnection := mqtt.NewBroker(config.remoteAddress)

	subscriber := mqtt.NewSubscriber(config.executionMode, localConnection, remoteConnection)
	publisher := mqtt.NewPublisher(localConnection, remoteConnection)

	go publisher.Start()

	flink := flink.NewFlink(config.flinkAddress, config.jarId, config.standaloneJarPath, config.executionMode)

	err := localConnection.Start()
	if err == nil {
		log.Println("mqtt: local: connected")
	}

	if config.executionMode == "edge" {
		err = remoteConnection.Start()
		if err == nil {
			log.Println("mqtt: remote: connected")
		}
	}

	var test chan bool

	if config.executionMode == "edge" {
		edgeRunner := runner.NewEdge(subscriber, publisher, flink, config.timeout, config.mlEnabled)
		subscriber.OnApplicationName(edgeRunner.SetApplication)
		edgeRunner.Start()
	} else {
		cloudRunner := runner.NewCloud(subscriber, publisher, flink)
		subscriber.OnApplicationName(cloudRunner.SetApplication)
		cloudRunner.Start()
	}

	<-test
}
