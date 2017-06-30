package main

import (
	"testing"
)

func TestGetDiskProperties1(t *testing.T) {
	diskSize, err := getDiskProperties("Disk /dev/sda: 477 GiB, 512110190592 bytes, 1000215216 sectors")

	if err != nil {
		t.Fail()
	}

	if diskSize.SizeBytes != 512110190592 {
		t.Fail()
	}

	if diskSize.Path != "/dev/sda" {
		t.Fail()
	}

}

func TestGetDiskProperties2(t *testing.T) {
	diskSize, err := getDiskProperties("Disk /dev/sdb: 2.9 TiB, 3200527458304 bytes, 6251030192 sectors")

	if err != nil {
		t.Fail()
	}

	if diskSize.SizeBytes != 3200527458304 {
		t.Fail()
	}

	if diskSize.Path != "/dev/sdb" {
		t.Fail()
	}

}
