package main

import (
	"net"
	"strings"
	"strconv"
)

type Iface struct {
	IPv4    string
	CIDRv4  string
	Netmask int        `json:"netmask"`
	MAC     string
	Name    string     `json:"name"`
}

func IsCIDRv4(cidr string) bool {
	i, _, err := net.ParseCIDR(cidr)
	if err != nil {
		return false
	}
	if i.To4() == nil {
		return false
	}
	return true
}

func GetIPv4Netmask(cidr string) (ip string, mask int) {
	split := strings.Split(cidr, "/")

	ip = split[0]
	mask, _ = strconv.Atoi(split[1])
	return
}

func LocalIfaces() []Iface {
	var ifaces []Iface
	var iface Iface
	var addrs []net.Addr
	var err error

	interfaces, _ := net.Interfaces()

	for _, i := range interfaces {

		addrs, err = i.Addrs()
		if err != nil {
			continue
		}
		iface.Name = i.Name
		iface.MAC = i.HardwareAddr.String()
		for _, a := range addrs {
			if IsCIDRv4(a.String()) {
				iface.CIDRv4 = a.String()
				iface.IPv4, iface.Netmask =
					GetIPv4Netmask(a.String())
			}
		}
		ifaces = append(ifaces, iface)
	}
	return ifaces
}
