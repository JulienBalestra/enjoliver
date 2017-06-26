package main

import (
	"github.com/vishvananda/netlink"
	"net"
	"strconv"
	"strings"
	"github.com/golang/glog"
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

const externalRoute = "8.8.8.8"

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

func GetIPv4Netmask(cidr string) (ip string, mask int, err error) {
	split := strings.Split(cidr, "/")

	ip = split[0]
	mask, err = strconv.Atoi(split[1])
	return ip, mask, err
}

func LocalIfaces() (ifaces []Iface, err error) {
	var iface Iface
	var addrs []net.Addr

	interfaces, err := net.Interfaces()
	if err != nil {
		return ifaces, err
	}

	for i, interf := range interfaces {

		addrs, err = interf.Addrs()
		if err != nil {
			glog.Warningf("skipping interface %d: %s", i, err)
			continue
		}
		iface.Name = interf.Name
		iface.MAC = interf.HardwareAddr.String()
		for _, a := range addrs {
			if IsCIDRv4(a.String()) {
				iface.CIDRv4 = a.String()
				iface.IPv4, iface.Netmask, err = GetIPv4Netmask(a.String())
				if err != nil {
					glog.Errorf("fail to get IP and netmask: %s", err)
					return ifaces, err
				}
				route, err := netlink.RouteGet(net.ParseIP(externalRoute))
				if err != nil {
					glog.Warningf("fail to get route for %s", externalRoute)
				}
				iface.Gateway = route[0].Gw.String()
				iface.Fqdn, err = net.LookupAddr(iface.IPv4)
				if err != nil {
					glog.Warningf("fail to get DNS for %s", iface.IPv4)
				}
			}
		}
		ifaces = append(ifaces, iface)
		glog.V(4).Infof("adding interface %s in %d interfaces", iface.Name, len(ifaces))
	}
	return ifaces, nil
}
