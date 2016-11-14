package main

import (
	"testing"
	"os"
)

func Test0ParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	CONF.ProcCmdline = "tests" + CONF.ProcCmdline + "0"

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

func Test1ParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	CONF.ProcCmdline = "tests" + CONF.ProcCmdline + "1"

	bi, err := ParseCommandLine()
	if err != nil {
		t.Errorf(err.Error())
	}
	if bi.Uuid != "ee378e7b-1575-425d-a6d6-e0dadb9f31a0" {
		t.Error(bi.Uuid)
	}
	if bi.Mac != "52:54:00:90:c3:9f" {
		t.Error(bi.Mac)
	}
}


func Test2ParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	CONF.ProcCmdline = "tests" + CONF.ProcCmdline + "2"

	bi, err := ParseCommandLine()
	if err != nil {
		t.Errorf(err.Error())
	}
	if bi.Uuid != "62b58ffd-7960-419a-8359-91def082191a" {
		t.Error(bi.Uuid)
	}
	if bi.Mac != "52:54:00:71:83:ea" {
		t.Error(bi.Mac)
	}
}

