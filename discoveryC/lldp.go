package main

import (
	"encoding/xml"
	"io/ioutil"
	"log"
)

type LLDPData struct {
	IsFile bool  `json:"is_file"`
	Data   XLLDP `json:"data"`
}

type XLLDP struct {
	Interfaces []XInterface `xml:"interface" json:"interfaces"`
}

type XInterface struct {
	Port    XPort    `xml:"port" json:"port"`
	Chassis XChassis `xml:"chassis" json:"chassis"`
	Name    string   `xml:"name,attr" json:"name"`
}

type XPort struct {
	Id string `xml:"id" json:"id"`
}

type XChassis struct {
	Id   string `xml:"id" json:"id"`
	Name string `xml:"name" json:"name"`
}

func extractXMLLinkLayerDiscovery(b []byte) XLLDP {
	var l XLLDP

	e := xml.Unmarshal(b, &l)
	if e != nil {
		log.Println(e)
		return l
	}
	return l
}

func (c *Config) ParseLLDPFile() LLDPData {
	var lldp LLDPData

	b, err := ioutil.ReadFile(c.LLDPFile)

	if err != nil {
		// no file no LLDP
		lldp.IsFile = false
		log.Println(err)
		return lldp
	}
	lldp.IsFile = true
	lldp.Data = extractXMLLinkLayerDiscovery(b)
	return lldp
}
