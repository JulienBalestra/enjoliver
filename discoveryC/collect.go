package main

type DiscoveryData struct {
	Interfaces []Iface `json:"interfaces"`
	BootInfo   BootInfo `json:"boot-info"`
	LLDPInfo   LLDPData `json:"lldp"`
}

func CollectData() DiscoveryData {
	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	data.BootInfo, _ = ParseCommandLine()
	data.LLDPInfo = ParseLLDPFile()
	return data
}
