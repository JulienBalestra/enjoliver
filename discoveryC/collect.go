package main

import "github.com/golang/glog"

type DiscoveryData struct {
	Interfaces      []Iface          `json:"interfaces"`
	Disks           []DiskProperties `json:"disks"`
	BootInfo        BootInfo         `json:"boot-info"`
	LLDPInfo        LLDPData         `json:"lldp"`
	IgnitionJournal []string         `json:"ignition-journal"`
}

func (c *Config) CollectData() (data DiscoveryData, err error) {
	glog.V(2).Infof("starting collecting data")

	data.Disks, err = GetDisks()
	if err != nil {
		glog.Errorf("fail to get storage: %s", err)
		return data, err
	}

	data.Interfaces, err = LocalIfaces()
	if err != nil {
		glog.Errorf("fail to get interfaces: %s", err)
		return data, err
	}

	data.BootInfo, err = c.ParseCommandLine()
	if err != nil {
		glog.Warningf("fail to parse cmdline: %s getting metadata file instead", err)
		data.BootInfo, err = c.ParseMetadata()
		if err != nil {
			glog.Errorf("fail to parse metadata: %s", err)
			return data, err
		}
	}

	// LLDP is not error managed
	data.LLDPInfo = c.ParseLLDPFile()

	data.IgnitionJournal, err = c.GetIgnitionJournal()
	if err != nil {
		glog.Errorf("fail to get ignition journal: %s", err)
		return data, err
	}

	return data, nil
}
