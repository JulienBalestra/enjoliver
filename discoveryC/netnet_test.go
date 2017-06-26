package main

import (
	"testing"
)

func TestIsIPv4(t *testing.T) {
	if IsCIDRv4("192.168.1.1/24") == false {
		t.Fail()
	}
	if IsCIDRv4("fe80::7c80:8fff:fe8a:3709/64") == true {
		t.Fail()
	}
}

func TestGetIPv4Netmask(t *testing.T) {
	ip, mask, err := GetIPv4Netmask("192.168.1.1/24")
	if err != nil {
		t.Fail()
	}
	if ip != "192.168.1.1" {
		t.Fail()
	}
	if mask != 24 {
		t.Fail()
	}
}

func TestLocalIfaces(t *testing.T) {
	var ok bool = false
	ips, err := LocalIfaces()
	if err != nil {
		t.Error(err)
	}
	for _, i := range ips {
		if i.CIDRv4 == "127.0.0.1/8" {
			ok = true
		}
	}
	if ok == false {
		t.Fail()
	}
}
