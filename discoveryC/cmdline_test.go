package main

import (
	"testing"
	"os"
)

func TestParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	CONF.ProcCmdline = "tests" + CONF.ProcCmdline

	bi, err := ParseCommandLine()
	if err != nil {
		t.Errorf(err.Error())
	}
	if bi.Uuid != "2023e709-39b4-47d7-8905-e8be3e6bc2c6" {
		t.Error(bi.Uuid)
	}
	if bi.Mac != "52:54:00:0d:bd:31" {
		t.Error(bi.Mac)
	}
}

