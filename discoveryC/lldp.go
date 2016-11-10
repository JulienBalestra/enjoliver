package main

import (
	"io/ioutil"
	"log"
	"encoding/xml"
)

type LLDPData struct {
	IsFile bool
	Data XLLDP
}

type XLLDP struct {
	Interfaces []XInterface `xml:"interface"`
}

type XInterface struct {
	Port XPort `xml:"port"`
	Chassis XChassis `xml:"chassis"`
}

type XPort struct {
	Id string `xml:"id"`
}

type XChassis struct {
	Id string `xml:"id"`
	Name string `xml:"name"`
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

func ParseLLDPFile() LLDPData {
	var lldp LLDPData

	b, err := ioutil.ReadFile(CONF.LLDPFile)

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
