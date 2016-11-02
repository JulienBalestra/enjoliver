package main

import (
	"log"
)

var CONF Config

type DiscoveryData struct {
	Interfaces []Iface `json:"interfaces"`
}

func main() {
	var err error
	CONF, err = CreateConfig()
	if err != nil {
		log.Fatal(err)
		return
	}
	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	err = PostToDiscovery(data)
	if err != nil {
		log.Fatal(err)
	}
	return
}