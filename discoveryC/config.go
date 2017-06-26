package main

import (
	"os"
	"github.com/golang/glog"
	"fmt"
)

type Config struct {
	// http://IP:PORT
	DiscoveryAddress  string
	ProcCmdline       string
	EnjoliverMetadata string
	ProcBootId        string
	LLDPFile          string
	IgnitionFile      string
}

func CreateConfig() (*Config, error) {
	var c Config

	c.DiscoveryAddress = os.Getenv("DISCOVERY_ADDRESS")
	if c.DiscoveryAddress == "" {
		return nil, fmt.Errorf("Environment DISCOVERY_ADDRESS is nil")
	}

	LLDPFileDefault := "/run/lldp/lldp.xml"
	c.LLDPFile = os.Getenv("LLDP_FILE")
	if c.LLDPFile == "" {
		glog.V(2).Infof("Environment LLDP_FILE is nil setting default: %s", LLDPFileDefault)
		c.LLDPFile = LLDPFileDefault
	}

	IgnitionFileDefault := "/run/ignition.journal"
	c.IgnitionFile = os.Getenv("IGNITION_FILE")
	if c.IgnitionFile == "" {
		glog.V(2).Infof("Environment IGNITION_FILE is nil setting default: %s", IgnitionFileDefault)
		c.IgnitionFile = IgnitionFileDefault
	}

	ProcCmdlineDefault := "/proc/cmdline"
	c.ProcCmdline = os.Getenv("PROC_CMDLINE")
	if c.ProcCmdline == "" {
		glog.V(2).Infof("Environment PROC_CMDLINE is nil setting default: %s", ProcCmdlineDefault)
		c.ProcCmdline = ProcCmdlineDefault
	}

	EnjoliverMetadata := "/etc/metadata.env"
	c.EnjoliverMetadata = os.Getenv("METADATA_ENV")
	if c.EnjoliverMetadata == "" {
		glog.V(2).Infof("Environment METADATA_ENV is nil setting default: %s", ProcCmdlineDefault)
		c.EnjoliverMetadata = EnjoliverMetadata
	}

	BootIdDefault := "/proc/sys/kernel/random/boot_id"
	c.ProcBootId = os.Getenv("PROC_BOOT_ID")
	if c.ProcBootId == "" {
		glog.V(2).Infof("Environment PROC_BOOT_ID is nil setting default: %s", BootIdDefault)
		c.ProcBootId = BootIdDefault
	}
	return &c, nil
}
