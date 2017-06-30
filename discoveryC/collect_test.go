package main

import (
	"os"
	"testing"
)

func TestCollectData(t *testing.T) {
	c, err := CreateConfig()
	if err != nil {
		t.Error(err)
	}
	c.IgnitionFile = "tests/run/ignition.journal0"
	c.ProcCmdline = "tests/proc/cmdline0"
	c.LLDPFile = "tests/run/lldp/output2.xml"
	data, err := c.CollectData()

	if len(data.Interfaces) < 1 {
		t.Error("len(data.Interfaces) < 1")
	}
	if data.BootInfo.Mac == "" {
		t.Error("Mac is null")
	}
	if data.BootInfo.Uuid == "" {
		t.Error("Uuid is null")
	}
	if data.LLDPInfo.IsFile != true {
		t.Error("data.LLDPInfo.IsFile is false")
	}
	if len(data.LLDPInfo.Data.Interfaces) == 0 {
		t.Error("len(data.LLDPInfo.Data.Interfaces) == 0")
	}
	if len(data.IgnitionJournal) != 42 {
		t.Error("IgnitionJournal", len(data.IgnitionJournal))
	}

	// quick hack to avoid interfaces to only test fdisk behavior
	if os.Geteuid() == 0 && err != nil {
		t.Error(err)
	}
}
