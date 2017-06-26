package main

import (
	"github.com/vishvananda/netlink"
	"log"
	"net"
	"strconv"
	"strings"
)

type Iface struct {
	IPv4    string   `json:"ipv4"`
	CIDRv4  string   `json:"cidrv4"`
	Netmask int      `json:"netmask"`
	MAC     string   `json:"mac"`
	Name    string   `json:"name"`
	Gateway string   `json:"gateway"`
	Fqdn    []string `json:"fqdn"`
}

const externalRoute  = "8.8.8.8"

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

func LocalIfaces() (ifaces []Iface, err error) {
	var iface Iface
	var addrs []net.Addr

	interfaces, err := net.Interfaces()
	if err != nil {
		return ifaces, err
	}

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
				route, err := netlink.RouteGet(net.ParseIP(externalRoute))
				if err != nil {
					log.Printf("fail to get route for %s", externalRoute)
				}
				iface.Gateway = route[0].Gw.String()
				iface.Fqdn, err = net.LookupAddr(iface.IPv4)
				if err != nil {
					log.Printf("fail to get DNS for %s", iface.IPv4)
				}
			}
		}
		ifaces = append(ifaces, iface)
	}
	return ifaces, nil
}
