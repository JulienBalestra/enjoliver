package main

import (
	"os"
	"testing"
)

func Test2LLDPParse(t *testing.T) {
	os.Setenv("LLDP_FILE", "tests/run/lldp/output2.xml")
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := c.ParseLLDPFile()
	if len(result.Data.Interfaces) != 2 {
		t.Error("len(result.Data.Interfaces) != 2")
	}
}

func Test1LLDPParse(t *testing.T) {
	os.Setenv("LLDP_FILE", "tests/run/lldp/output1.xml")
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := c.ParseLLDPFile()
	if len(result.Data.Interfaces) != 1 {
		t.Error("len(result.Data.Interfaces) != 1")
	}
}

func Test0LLDPParse(t *testing.T) {
	os.Setenv("LLDP_FILE", "tests/run/lldp/output0.xml")
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := c.ParseLLDPFile()
	if len(result.Data.Interfaces) != 0 {
		t.Error("len(result.Data.Interfaces) != 1")
	}
}

func TestNoLLDPParse(t *testing.T) {
	os.Setenv("LLDP_FILE", "tests/run/lldp/nohere.xml")
	c, err := CreateConfig()
	if err != nil {
		t.Fail()
	}
	result := c.ParseLLDPFile()
	if len(result.Data.Interfaces) != 0 {
		t.Error("len(result.Data.Interfaces) != 1")
	}
	if result.IsFile != false {
		t.Error("len(result.IsFile) != false")
	}
}
