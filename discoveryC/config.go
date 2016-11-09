package main

import (
	"os"
	"errors"
	"log"
)

type Config struct {
	// http://IP:PORT
	DiscoveryAddress string
	ProcCmdline      string
	LLDPFile      string
}

func CreateConfig() (Config, error) {
	var c Config

	c.DiscoveryAddress = os.Getenv("DISCOVERY_ADDRESS")
	if (c.DiscoveryAddress == "") {
		return c, errors.New("Environment DISCOVERY_ADDRESS is nil")
	}

	c.LLDPFile = os.Getenv("LLDP_FILE")
	if (c.LLDPFile == "") {
		log.Println("Environment LLDP_FILE is nil")
	}

	c.ProcCmdline = "/proc/cmdline"
	return c, nil
}