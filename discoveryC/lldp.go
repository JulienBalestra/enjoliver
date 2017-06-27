package main

import (
	"encoding/xml"
	"github.com/golang/glog"
	"io/ioutil"
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

func extractXMLLinkLayerDiscovery(b []byte) (XLLDP, error) {
	var l XLLDP

	err := xml.Unmarshal(b, &l)
	if err != nil {
		glog.Errorf("fail to unmarshal %s: %s", string(b), err)
		return l, err
	}
	return l, nil
}

func (c *Config) ParseLLDPFile() LLDPData {
	var lldp LLDPData

	b, err := ioutil.ReadFile(c.LLDPFile)

	if err != nil {
		// no file no LLDP
		lldp.IsFile = false
		glog.Warningf("fail to open LLDP file: ignoring", c.LLDPFile)
		return lldp
	}
	lldp.IsFile = true
	lldp.Data, err = extractXMLLinkLayerDiscovery(b)
	if err != nil {
		glog.Warningf("fail to extract data from LLDP file %s: ignoring", c.LLDPFile)
		lldp.IsFile = false
	}
	return lldp
}
