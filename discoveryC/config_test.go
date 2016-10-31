package main

import (
	"testing"
	"os"
)

func TestConfig(t *testing.T) {
	//var c Config
	var discoAddress = "http://127.0.0.1:5000"
	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, _ := CreateConfig()
	if c.DiscoveryAddress != discoAddress {
		//t.Log("")
		t.Fail()
	}
}

