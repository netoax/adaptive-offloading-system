package flink

import (
	"fmt"
	"net/url"
)

type Flink struct {
	address *url.URL
	jobId   string
	jarId   string
	jarPath string
}

func NewFlink(address, jarId, jarPath string) *Flink {
	url, err := url.Parse(address)
	if err != nil {
		fmt.Println("cannot parse URL")
	}

	return &Flink{url, "", jarId, jarPath}
}
