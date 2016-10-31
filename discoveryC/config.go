package main

import (
	"os"
	"errors"
)

type Config struct {
	// http://IP:PORT
	DiscoveryAddress string
}

func CreateConfig() (Config, error) {
	var c Config

	c.DiscoveryAddress = os.Getenv("DISCOVERY_ADDRESS")
	if (c.DiscoveryAddress == "") {
		return c, errors.New("Environment DISCOVERY_ADDRESS is nil")
	}
	return c, nil
}