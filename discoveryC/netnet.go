package main

import (
	"net"
	"log"
	"strconv"
	"strings"
)

type Iface struct {
	IPv4    string
	CIDR    string
	Netmask int
}

func LocalIfaces() []Iface {
	var ifaces []Iface
	var iface Iface

	interfaces, err := net.InterfaceAddrs()
	if err != nil {
		log.Println(err)
	}
	for _, i := range interfaces {
		ip, network, err := net.ParseCIDR(i.String())
		if err != nil {
			log.Println(err)
			continue
		}
		if !ip.IsLoopback() && ip.To4() != nil {
			iface.CIDR = network.String()
			iface.Netmask, _ = strconv.Atoi(strings.Split(network.String(), "/")[1])
			iface.IPv4 = ip.String()
			ifaces = append(ifaces, iface)
		}
	}
	log.Printf("%d ifaces", len(ifaces))
	return ifaces
}
