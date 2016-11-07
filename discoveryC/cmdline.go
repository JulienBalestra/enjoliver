package main

import (
	"io/ioutil"
	"log"
	"strings"
	"errors"
)

type BootInfo struct {
	Uuid string `json:"uuid"`
	Mac  string `json:"mac"`
}

func getCoreosConfigUrl(b []byte) (string, error) {
	str := string(b)
	fields := strings.Fields(str)
	for _, word := range fields {
		if strings.Contains(word, "coreos.config.url=") {
			line := strings.Trim(word, "coreos.config.url=")
			return line, nil
		}
	}
	return "", errors.New("No coreos.config.url=")
}

func getBootInfo(url string) (BootInfo, error) {
	var bi BootInfo
	var uuid string = "uuid="
	var mac string = "mac="

	query := strings.SplitAfter(url, "/ignition?")
	if len(query) != 2 {
		return bi, errors.New("incoherent SplitAfter(url, \"/ignition?\") != 2")
	}
	args := strings.Split(query[1], "&")
	for _, arg := range args {
		if strings.Contains(arg, uuid) {
			bi.Uuid = strings.Trim(arg, uuid)
		}
		if strings.Contains(arg, mac) {
			bi.Mac = strings.Trim(arg, mac)
			bi.Mac = strings.Replace(bi.Mac, "-", ":", -1)
		}
	}
	return bi, nil
}

func ParseCommandLine() (BootInfo, error) {
	var bi BootInfo
	b, err := ioutil.ReadFile(CONF.ProcCmdline)
	if err != nil {
		log.Println(err)
		return bi, err
	}
	url, err := getCoreosConfigUrl(b)
	if err != nil {
		log.Println(err)
		return bi, err
	}
	return getBootInfo(url)
}