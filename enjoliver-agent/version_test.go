package main

import (
	"testing"
)

func TestGetStringInTable(t *testing.T) {
	rktOutput := `v Version: 1.25.0
appc Version: 0.8.10
Go Version: go1.7.4
Go OS/Arch: linux/amd64
Features: -TPM +SDJOURNAL
`
	v, err := getStringInTable(rktOutput, rktVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "1.25.0" {
		t.Errorf("fail to get version: %s", v)
	}

	hyperkubeOutput := "Kubernetes v1.6.2+477efc3\n"
	v, err = getStringInTable(hyperkubeOutput, hyperkubeVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v1.6.2+477efc3" {
		t.Errorf("fail to get version: %s", v)
	}

	etcdOutput := `etcd Version: 3.2.5
	Git SHA: d0d1a87
	Go Version: go1.8.3
	Go OS/Arch: linux/amd64
`
	v, err = getStringInTable(etcdOutput, etcdVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "3.2.5" {
		t.Errorf("fail to get version: %s", v)
	}

}
