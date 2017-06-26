package main

import (
	"os/exec"
	"github.com/golang/glog"
	"strings"
	"fmt"
	"strconv"
)

type DiskProperties struct {
	SizeBytes int
	Path string
}

const lineMatchPrefix  = "Disk /dev/sd"


func getDiskProperties(str string) (diskSize DiskProperties, err error) {

	fieldList := strings.Fields(str)

	// diskNameField e.g: "/dev/sda:"
	diskNameField := string(fieldList[1])
	if string(diskNameField[len(diskNameField) - 1]) != ":" {
		glog.Errorf("incoherent parsing of diskNameField: %q", diskNameField)
		return diskSize, fmt.Errorf("incoherent parsing of diskNameField: %q", diskNameField)
	}
	diskSize.Path = diskNameField[:len(diskNameField) - 1]

	diskSizeBytesField := string(fieldList[5])
	diskSize.SizeBytes, err = strconv.Atoi(diskSizeBytesField)
	if err != nil {
		glog.Errorf("incoherent parsing of diskSizeBytesField: %s %s", diskSizeBytesField, err)
		return diskSize, err
	}

	return diskSize, nil
}


func GetDisks() (diskSizeList []DiskProperties, err error) {
	var disk DiskProperties

	out, err := exec.Command("fdisk", "-l").Output()
	if err != nil {
		glog.Errorf("fail to get the output of fdisk command: %s", err)
		return diskSizeList, err
	}
	for _, line := range strings.Split(string(out), "\n") {
		if strings.HasPrefix(line, lineMatchPrefix) {
			disk, err = getDiskProperties(line)
			if err != nil {
				glog.Errorf("fail to get disk properties")
			}
			diskSizeList = append(diskSizeList, disk)
			glog.V(4).Infof("added disk %q %d", disk.Path, disk.SizeBytes)
		}
	}
	return diskSizeList, nil
}
