package main

import (
	"fmt"
	"github.com/golang/glog"
	"os/exec"
	"strconv"
	"strings"
)

type DiskProperties struct {
	SizeBytes int    `json:"size-bytes"`
	Path      string `json:"path"`
}

const lineMatchPrefix = "Disk /dev/sd"

func getDiskProperties(str string) (diskSize DiskProperties, err error) {

	fieldList := strings.Split(str, " ")

	glog.V(3).Infof("parsing %q", str)
	// diskNameField e.g: "/dev/sda:"
	diskNameField := string(fieldList[1])
	if diskNameField[len(diskNameField)-1] != ':' {
		glog.Errorf("incoherent parsing of diskNameField: %q", diskNameField)
		return diskSize, fmt.Errorf("incoherent parsing of diskNameField: %q", diskNameField)
	}
	diskSize.Path = diskNameField[:len(diskNameField)-1]

	diskSizeBytesField := string(fieldList[4])
	diskSize.SizeBytes, err = strconv.Atoi(diskSizeBytesField)
	if err != nil {
		glog.Errorf("incoherent parsing of diskSizeBytesField: %q %s", diskSizeBytesField, err)
		return diskSize, err
	}

	return diskSize, nil
}

func GetDisks() (diskSizeList []DiskProperties, err error) {
	var disk DiskProperties

	out, err := exec.Command("fdisk", "-l").Output()
	glog.V(5).Infof("fdisk -l %q", out)
	if err != nil {
		glog.Errorf("fail to get the output of fdisk command: %s", err)
		return diskSizeList, err
	}
	if len(out) == 0 {
		glog.Errorf("fail to get the output of fdisk command: empty")
		return diskSizeList, fmt.Errorf("fail to get output of fdisk -l")
	}
	for _, line := range strings.Split(string(out), "\n") {
		if strings.HasPrefix(line, lineMatchPrefix) {
			disk, err = getDiskProperties(line)
			if err != nil {
				glog.Errorf("fail to get disk properties")
				continue
			}
			diskSizeList = append(diskSizeList, disk)
			glog.V(2).Infof("added disk %q %d", disk.Path, disk.SizeBytes)
		}
	}
	return diskSizeList, nil
}
