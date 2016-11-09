package main

import (
	"io/ioutil"
	"log"
	"strings"
)

type LLDPInfo struct {
	File     bool
	Lines    int
	Connects []string
}

func getLLDPPortIfname(b []byte) LLDPInfo {
	var lldp LLDPInfo

	// with []byte where is a file
	lldp.File = true

	str := string(b)
	lines := strings.Split(str, "\n")
	lldp.Lines = len(lines)
	log.Printf("lldp.lines=%v", lldp.Lines)

	if lldp.Lines < 2 {
		log.Println("lldp.Lines < 2")
		return lldp
	}

	for _, line := range lines {
		if strings.Contains(line, "port.ifname=") == true {
			log.Printf("port.ifname match: %s", line)
			lldp.Connects = append(lldp.Connects, line)
		}
	}
	log.Printf("lldp.connects=%v", len(lldp.Connects))
	return lldp
}

func ParseLLDPFile() LLDPInfo {
	var lldp LLDPInfo

	b, err := ioutil.ReadFile(CONF.LLDPFile)

	if err != nil {
		// no file no LLDP
		lldp.File = false
		log.Println(err)
		return lldp
	}
	lldp = getLLDPPortIfname(b)
	return lldp
}
