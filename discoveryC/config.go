package main

import (
	"errors"
	"log"
	"os"
)

type Config struct {
	// http://IP:PORT
	DiscoveryAddress string
	ProcCmdline      string
	ProcBootId       string
	LLDPFile         string
	IgnitionFile     string
}

func CreateConfig() (Config, error) {
	var c Config

	c.DiscoveryAddress = os.Getenv("DISCOVERY_ADDRESS")
	if c.DiscoveryAddress == "" {
		return c, errors.New("Environment DISCOVERY_ADDRESS is nil")
	}

	LLDPFileDefault := "/run/lldp/lldp.xml"
	c.LLDPFile = os.Getenv("LLDP_FILE")
	if c.LLDPFile == "" {
		log.Printf("Environment LLDP_FILE is nil setting default: %s", LLDPFileDefault)
		c.LLDPFile = LLDPFileDefault
	}

	IgnitionFileDefault := "/run/ignition.journal"
	c.IgnitionFile = os.Getenv("IGNITION_FILE")
	if c.IgnitionFile == "" {
		log.Printf("Environment IGNITION_FILE is nil setting default: %s", IgnitionFileDefault)
		c.IgnitionFile = IgnitionFileDefault
	}

	ProcCmdlineDefault := "/proc/cmdline"
	c.ProcCmdline = os.Getenv("PROC_CMDLINE")
	if c.ProcCmdline == "" {
		log.Printf("Environment PROC_CMDLINE is nil setting default: %s", ProcCmdlineDefault)
		c.ProcCmdline = ProcCmdlineDefault
	}

	BootIdDefault := "/proc/sys/kernel/random/boot_id"
	c.ProcBootId = os.Getenv("PROC_BOOT_ID")
	if c.ProcBootId == "" {
		log.Printf("Environment PROC_BOOT_ID is nil setting default: %s", BootIdDefault)
		c.ProcBootId = BootIdDefault
	}
	return c, nil
}
