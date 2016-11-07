package main

type DiscoveryData struct {
	Interfaces []Iface `json:"interfaces"`
	BootInfo   BootInfo `json:"boot-info"`
}

func CollectData() DiscoveryData {
	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	data.BootInfo, _ = ParseCommandLine()
	return data
}
