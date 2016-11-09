package main

import (
	"testing"
	"os"
)

func Test0LLDPParse(t *testing.T) {
	//var c Config
	var err error

	os.Setenv("LLDP_FILE", "tests/run/lldp/lldp.kv.0")
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := ParseLLDPFile()
	if len(result.Connects) != 0 {
		t.Fail()
	}
}

func Test1LLDPParse(t *testing.T) {
	//var c Config
	var err error

	os.Setenv("LLDP_FILE", "tests/run/lldp/lldp.kv.1")
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := ParseLLDPFile()
	//println(result)
	if len(result.Connects) != 2 {
		t.Fail()
	}
}

func Test2LLDPParse(t *testing.T) {
	//var c Config
	var err error

	os.Setenv("LLDP_FILE", "tests/run/lldp/lldp.kv.2")
	CONF, err = CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := ParseLLDPFile()
	if len(result.Connects) != 0 {
		t.Fail()
	}
}

