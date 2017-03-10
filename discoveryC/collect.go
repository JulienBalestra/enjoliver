package main

type DiscoveryData struct {
	Interfaces      []Iface  `json:"interfaces"`
	BootInfo        BootInfo `json:"boot-info"`
	LLDPInfo        LLDPData `json:"lldp"`
	IgnitionJournal []string `json:"ignition-journal"`
}

func CollectData() DiscoveryData {
	var err error

	data := DiscoveryData{}
	data.Interfaces = LocalIfaces()
	data.BootInfo, err = ParseCommandLine()
	if err != nil {
		data.BootInfo, _ = ParseMetadata()
	}
	data.LLDPInfo = ParseLLDPFile()
	data.IgnitionJournal = GetIgnitionJournal()
	return data
}
