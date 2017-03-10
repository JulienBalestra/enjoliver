package main

import (
	"errors"
	"io/ioutil"
	"log"
	"strings"
)

type BootInfo struct {
	Uuid     string `json:"uuid"`
	Mac      string `json:"mac"`
	RandomId string `json:"random-id"`
}

func getCoreosConfigUrl(b []byte) (string, error) {
	prefix := "coreos.config.url="
	str := string(b)
	fields := strings.Fields(str)
	for _, word := range fields {
		if strings.Contains(word, prefix) {
			line := strings.Split(word, prefix)[1]
			return line, nil
		}
	}
	return "", errors.New("No coreos.config.url=")
}

func getRandomId() string {
	b, err := ioutil.ReadFile(CONF.ProcBootId)
	if err != nil {
		log.Println(err)
		return ""
	}
	str := string(b)
	str = strings.Trim(str, "\n")
	return str

}

func getBootInfoFromUrl(url string) (BootInfo, error) {
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
			bi.Uuid = strings.Split(arg, uuid)[1]
		}
		if strings.Contains(arg, mac) {
			bi.Mac = strings.Split(arg, mac)[1]
			bi.Mac = strings.Replace(bi.Mac, "-", ":", -1)
		}
	}
	bi.RandomId = getRandomId()
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
	return getBootInfoFromUrl(url)
}

/*
REQUEST_RAW_QUERY='uuid=673cdde4-2f54-417b-ad7f-3909c0faee59&mac=52-54-00-74-17-9d&os=installed'
*/
func getBootInfoFromMetadata(b []byte) (BootInfo, error) {
	var bi BootInfo
	prefix := "REQUEST_RAW_QUERY="
	str := string(b)
	fields := strings.Fields(str)
	for _, word := range fields {
		if strings.Contains(word, prefix) {
			line := strings.Split(word, prefix)[1]
			line = strings.Replace(line, "'", "", -1)
			selectors := strings.Split(line, "&")
			for _, selector := range selectors {
				kv := strings.Split(selector, "=")
				if kv[0] == "uuid" {
					bi.Uuid = kv[1]
				} else if kv[0] == "mac" {
					bi.Mac = strings.Replace(kv[1], "-", ":", -1)
				}
			}
			bi.RandomId = getRandomId()
			return bi, nil
		}
	}
	return bi, errors.New("No REQUEST_RAW_QUERY")
}

func ParseMetadata() (BootInfo, error) {
	var bi BootInfo
	b, err := ioutil.ReadFile(CONF.EnjoliverMetadata)
	if err != nil {
		return bi, err
	}
	return getBootInfoFromMetadata(b)
}
