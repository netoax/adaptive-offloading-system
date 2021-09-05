package system

import (
	"fmt"
	"log"

	iperf "github.com/BGrewell/go-iperf"
	ping "github.com/go-ping/ping"
)

type NetworkProfClient struct {
	address string
	client  *iperf.Client
}

type networkProfServer struct {
	port int
}

func NewNetworkProfilerClient(address string) NetworkProfClient {
	return NetworkProfClient{address: address}
}

func NewNetworkProfilerServer() networkProfServer {
	return networkProfServer{}
}

func (npc *NetworkProfClient) Start() error {
	c := iperf.NewClient(npc.address)
	c.SetStreams(1)
	c.SetTimeSec(10)
	c.SetInterval(1)

	npc.client = c

	err := npc.client.Start()
	if err != nil {
		return err
	}

	<-npc.client.Done

	return nil
}

func (nps *networkProfServer) Start() error {
	s := iperf.NewServer()
	err := s.Start()
	if err != nil {
		fmt.Printf("failed to start server: %v\n", err)
		return err
	}

	log.Println("iperf server started")

	return nil
}

func (npc *NetworkProfClient) GetBandwidthMbps() (float64, error) {
	npc.Start()
	result := npc.client.Report().End.SumReceived.BitsPerSecond / 1000000
	return float64(int(result*100)) / 100, nil
}

func (npc *NetworkProfClient) GetAverageRtt() (float64, error) {
	pinger, err := ping.NewPinger(npc.address)
	if err != nil {
		return 0, err
	}

	pinger.Count = 3
	err = pinger.Run()
	if err != nil {
		return 0, err
	}

	stats := pinger.Statistics()
	return stats.MaxRtt.Seconds(), nil
}
