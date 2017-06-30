package main

import (
	"os"
	"testing"
)

func TestConfig(t *testing.T) {
	//var c Config
	var discoAddress = "http://127.0.0.1:5000"
	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, err := CreateConfig()
	if err != nil {
		t.Error(err)
	}
	if c.DiscoveryAddress != discoAddress {
		t.Fail()
	}
}
