package main

type DiscoveryData struct {
	Interfaces []Iface `json:"interfaces"`
}

func CollectData() DiscoveryData {
	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	return data
}
