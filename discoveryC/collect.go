package main

type DiscoveryData struct {
	Interfaces      []Iface `json:"interfaces"`
	BootInfo        BootInfo `json:"boot-info"`
	LLDPInfo        LLDPData `json:"lldp"`
	IgnitionJournal []string `json:"ignition-journal"`
}

func CollectData() DiscoveryData {
	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	data.BootInfo, _ = ParseCommandLine()
	data.LLDPInfo = ParseLLDPFile()
	data.IgnitionJournal = GetIgnitionJournal()
	return data
}
