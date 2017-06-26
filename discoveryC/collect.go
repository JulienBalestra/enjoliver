package main


type DiscoveryData struct {
	Interfaces      []Iface  `json:"interfaces"`
	BootInfo        BootInfo `json:"boot-info"`
	LLDPInfo        LLDPData `json:"lldp"`
	IgnitionJournal []string `json:"ignition-journal"`
}

func (c *Config) CollectData() (data DiscoveryData, err error) {
	data.Interfaces, err = LocalIfaces()
	data.BootInfo, err = c.ParseCommandLine()
	if err != nil {
		data.BootInfo, err = c.ParseMetadata()
		if err != nil {
			return data, err
		}
	}
	data.LLDPInfo = c.ParseLLDPFile()
	data.IgnitionJournal, err = c.GetIgnitionJournal()
	if err != nil {
		return data, err
	}
	return data, nil
}
