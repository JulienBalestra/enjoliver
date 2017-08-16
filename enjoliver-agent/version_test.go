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

	ipOutput := "ip utility, iproute2-ss151103\n"
	v, err = getStringInTable(ipOutput, iproute2Version)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "iproute2-ss151103" {
		t.Errorf("fail to get version: %s", v)
	}

	vaultOutput := "Vault v0.8.0 ('af63d879130d2ee292f09257571d371100a513eb')\n"
	v, err = getStringInTable(vaultOutput, vaultVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v0.8.0" {
		t.Errorf("fail to get version: %s", v)
	}

	sdOutput := `systemd 233
	+PAM +AUDIT +SELINUX +IMA -APPARMOR +SMACK -SYSVINIT +UTMP +LIBCRYPTSETUP +GCRYPT -GNUTLS -ACL +XZ -LZ4 +SECCOMP +BLKID -ELFUTILS +KMOD -IDN default-hierarchy=legacy
`
	v, err = getStringInTable(sdOutput, systemdVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "233" {
		t.Errorf("fail to get version: %s", v)
	}

	unameOutput := "4.11.9-coreos\n"
	v, err = getStringInTable(unameOutput, kernelVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "4.11.9-coreos" {
		t.Errorf("fail to get version: %s", v)
	}

	fleetOutput := "fleetd version v1.0.0\n"
	v, err = getStringInTable(fleetOutput, fleetVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v1.0.0" {
		t.Errorf("fail to get version: %s", v)
	}

}
