package main

import (
	"testing"
)

func TestLocalIfaces(t *testing.T) {
	ips := LocalIfaces()
	for _, i := range ips {
		if i.CIDR == "127.0.0.0/8" {
			t.Log("CIDR");
			t.Fail()
		}
		if len(i.IPv4) > 4 && i.IPv4[:4] == "127." {
			t.Log("127.");
			t.Fail()
		}
	}
}

