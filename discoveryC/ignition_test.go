package main

import (
	"testing"
	"os"
)

func Test0GetIgnitionJournal(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}

	CONF.IgnitionFile = "tests/run/ignition.journal0"
	lines := GetIgnitionJournal()
	if len(lines) != 43 {
		t.Fail()
	}
}


