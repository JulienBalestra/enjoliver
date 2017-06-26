package main

import (
	"errors"
	"io/ioutil"
	"log"
	"strings"
	"fmt"
)

type BootInfo struct {
	Uuid     string `json:"uuid"`
	Mac      string `json:"mac"`
	RandomId string `json:"random-id"`
}

const (
	coreosConfigUrl = "coreos.config.url="
	uuidField = "uuid="
	macField = "mac="
	rawQueryPrefix  = "REQUEST_RAW_QUERY="
)

// in the /proc/cmdline parse the line to get the coreos config url
func getCoreosConfigUrl(b []byte) (string, error) {
	str := string(b)
	fields := strings.Fields(str)
	for _, word := range fields {
		if strings.Contains(word, coreosConfigUrl) {
			line := strings.Split(word, coreosConfigUrl)[1]
			return line, nil
		}
	}
	return "", fmt.Errorf("Cannot find %q", coreosConfigUrl)
}

// randomID is the current boot ID
func (c *Config) getRandomId() (string, error) {
	b, err := ioutil.ReadFile(c.ProcBootId)
	if err != nil {
		log.Println(err)
		return "", err
	}
	str := string(b)
	str = strings.Trim(str, "\n")
	return str, nil

}

func (c *Config) getBootInfoFromUrl(url string) (bootInfo BootInfo, err error) {
	query := strings.SplitAfter(url, "/ignition?")
	if len(query) != 2 {
		return bootInfo, errors.New("incoherent SplitAfter(url, \"/ignition?\") != 2")
	}
	args := strings.Split(query[1], "&")
	for _, arg := range args {
		if strings.Contains(arg, uuidField) {
			bootInfo.Uuid = strings.Split(arg, uuidField)[1]
		}
		if strings.Contains(arg, macField) {
			bootInfo.Mac = strings.Split(arg, macField)[1]
			bootInfo.Mac = strings.Replace(bootInfo.Mac, "-", ":", -1)
		}
	}
	bootInfo.RandomId, err = c.getRandomId()
	if err != nil {
		return bootInfo, err
	}
	return bootInfo, nil
}

func (c *Config) ParseCommandLine() (BootInfo, error) {
	var bi BootInfo
	b, err := ioutil.ReadFile(c.ProcCmdline)
	if err != nil {
		log.Println(err)
		return bi, err
	}
	url, err := getCoreosConfigUrl(b)
	if err != nil {
		log.Println(err)
		return bi, err
	}
	return c.getBootInfoFromUrl(url)
}

/*
REQUEST_RAW_QUERY='uuid=673cdde4-2f54-417b-ad7f-3909c0faee59&mac=52-54-00-74-17-9d&os=installed'
*/
func (c *Config) getBootInfoFromMetadata(b []byte) (bootInfo BootInfo, err error) {
	str := string(b)
	fields := strings.Fields(str)
	for _, word := range fields {
		if strings.Contains(word, rawQueryPrefix) {
			line := strings.Split(word, rawQueryPrefix)[1]
			line = strings.Replace(line, "'", "", -1)
			selectors := strings.Split(line, "&")
			for _, selector := range selectors {
				kv := strings.Split(selector, "=")
				if kv[0] == "uuid" {
					bootInfo.Uuid = kv[1]
				} else if kv[0] == "mac" {
					bootInfo.Mac = strings.Replace(kv[1], "-", ":", -1)
				}
			}
			bootInfo.RandomId, err = c.getRandomId()
			if err != nil {
				return bootInfo, err
			}
			return bootInfo, nil
		}
	}
	return bootInfo, errors.New("No REQUEST_RAW_QUERY")
}

func (c *Config) ParseMetadata() (bootInfo BootInfo, err error) {
	b, err := ioutil.ReadFile(c.EnjoliverMetadata)
	if err != nil {
		return bootInfo, err
	}
	return c.getBootInfoFromMetadata(b)
}
