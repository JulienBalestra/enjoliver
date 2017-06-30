package main

import (
	"os"
	"testing"
)

func Test0GetIgnitionJournal(t *testing.T) {
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}

	c.IgnitionFile = "tests/run/ignition.journal0"
	lines, err := c.GetIgnitionJournal()
	if err != nil {
		t.Error(err)
	}
	if len(lines) != 42 {
		t.Error("")
	}
}
