package main

import (
	"os"
	"testing"
)

func Test0ParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	c.ProcCmdline = "tests" + c.ProcCmdline + "0"
	c.ProcBootId = "tests" + c.ProcBootId

	bi, err := c.ParseCommandLine()
	if err != nil {
		t.Errorf(err.Error())
	}
	if bi.Uuid != "2023e709-39b4-47d7-8905-e8be3e6bc2c6" {
		t.Error(bi.Uuid)
	}
	if bi.Mac != "52:54:00:0d:bd:31" {
		t.Error(bi.Mac)
	}
	if bi.RandomId != "3492b948-cec6-4d6f-b008-cc98bf03c9d3" {
		t.Error(bi.RandomId)
	}
}

func Test1ParseCommandLine(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	c.ProcCmdline = "tests" + c.ProcCmdline + "1"

	bi, err := c.ParseCommandLine()
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
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	c.ProcCmdline = "tests" + c.ProcCmdline + "2"

	bi, err := c.ParseCommandLine()
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

func Test3ParseMetadata(t *testing.T) {
	//var c Config
	var err error
	var discoAddress = "http://127.0.0.1:5000"

	os.Setenv("DISCOVERY_ADDRESS", discoAddress)
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	c.EnjoliverMetadata = "tests" + c.EnjoliverMetadata + "0"

	bi, err := c.ParseMetadata()
	if bi.Mac != "52:54:00:74:17:9d" {
		t.Error(bi.Mac)
	}
	if bi.Uuid != "673cdde4-2f54-417b-ad7f-3909c0faee59" {
		t.Error(bi.Mac)
	}
}
