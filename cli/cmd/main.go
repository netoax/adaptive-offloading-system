package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/url"
	"os"
	"strconv"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/urfave/cli"
)

var app = cli.NewApp()

func main() {
	info()
	commands()
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

func info() {
	// author := cli.Author{Name: "João Alexandre Neto", Email: "jasn3@cin.ufpe.br"}
	app.Name = "Orchestrator CLI"
	app.Usage = "An orchestrator CLI for testing purposes"
	// app.Authors = []*cli.Author{&author}
	app.Version = "1.0.0"
}

func commands() {
	app.Commands = []cli.Command{
		{
			Name:    "send-offloading-signal",
			Aliases: []string{"sos"},
			Usage:   "Send offloading signal to the orchestrator",
			Action:  offloadingSignalCommand,
		},
		{
			Name:    "stream",
			Aliases: []string{"s"},
			Usage:   "Simulate a data stream",
			Action:  streamCommand,
		},
		{
			Name:    "assessment",
			Aliases: []string{"s"},
			Usage:   "Send offloading classification assessment",
			Action:  offloadingAssessment,
		},
	}
}

func offloadingSignalCommand(c *cli.Context) error {
	value := c.Args().First()
	if value == "" {
		cli.ShowCommandHelp(c, "status")
		os.Exit(1)
	}

	b, err := strconv.ParseBool(value)
	if err != nil {
		log.Fatal(err)
	}
	publishOffloadingSignal(b)
	fmt.Println("Offloading signal published")
	return nil
}

func offloadingAssessment(c *cli.Context) error {
	latency := c.Args().Get(0)
	if latency == "" {
		cli.ShowCommandHelp(c, "latency")
		os.Exit(1)
	}

	cpu := c.Args().Get(1)
	if latency == "" {
		cli.ShowCommandHelp(c, "cpu")
		os.Exit(1)
	}

	memory := c.Args().Get(2)
	if latency == "" {
		cli.ShowCommandHelp(c, "memory")
		os.Exit(1)
	}

	lat, err := strconv.ParseFloat(latency, 0)
	cp, err := strconv.ParseFloat(cpu, 0)
	mem, err := strconv.ParseFloat(memory, 0)

	if err != nil {
		log.Fatal(err)
	}

	publishAssessment(lat, cp, mem)
	fmt.Println("Assessment result published")
	return nil
}

func streamCommand(c *cli.Context) error {
	uri, err := url.Parse("mqtt://localhost:1883")
	if err != nil {
		log.Fatal(err)
	}

	client := connect("abcde", uri)

	for {
		number := rand.Intn(100)
		client.Publish("/application/data", 0, false, string(number))
		fmt.Println("message published: " + strconv.Itoa(number))
		time.Sleep(5 * time.Second)
	}

	return nil
}

func publishOffloadingSignal(status bool) {
	uri, err := url.Parse("mqtt://localhost:1883")
	if err != nil {
		log.Fatal(err)
	}

	data := map[string]bool{
		"status": status,
	}

	dataJSON, err := json.Marshal(data)
	if err != nil {
		log.Fatal(err)
	}

	client := connect("abcde", uri)
	client.Publish("/prediction/offloading", 0, false, string(dataJSON))
}

func publishAssessment(latency, cpu, memory float64) {
	uri, err := url.Parse("mqtt://localhost:1883")
	if err != nil {
		log.Fatal(err)
	}

	data := map[string]interface{}{
		"latency": latency,
		"cpu":     cpu,
		"memory":  memory,
		"correct": true,
	}

	dataJSON, err := json.Marshal(data)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(data)

	client := connect("abaascde", uri)
	client.Publish("/assessment", 0, false, string(dataJSON))
}

func connect(clientID string, uri *url.URL) mqtt.Client {
	opts := createClientOptions(clientID, uri)
	client := mqtt.NewClient(opts)
	token := client.Connect()
	for !token.WaitTimeout(10 * time.Second) {
	}
	if err := token.Error(); err != nil {
		log.Fatal(err)
	}
	return client
}

func createClientOptions(clientID string, uri *url.URL) *mqtt.ClientOptions {
	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s", uri.Host))
	opts.SetUsername(uri.User.Username())
	password, _ := uri.User.Password()
	opts.SetPassword(password)
	opts.SetClientID(clientID)
	return opts
}

func listen(uri *url.URL, topic string) {
	client := connect("sub", uri)
	client.Subscribe(topic, 0, func(client mqtt.Client, msg mqtt.Message) {
		fmt.Printf("* [%s] %s\n", msg.Topic(), string(msg.Payload()))
	})
}
