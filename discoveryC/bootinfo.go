package main

import (
	"errors"
	"io/ioutil"
	"github.com/golang/glog"
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
	cmdline := string(b)
	glog.V(4).Infof("get %s in %q", coreosConfigUrl, cmdline)
	for i, word := range strings.Fields(cmdline) {
		if strings.Contains(word, coreosConfigUrl) {
			line := strings.Split(word, coreosConfigUrl)[1]
			glog.V(4).Infof("found %q at word %d", coreosConfigUrl, i)
			return line, nil
		}
	}
	return "", fmt.Errorf("Cannot find %q", coreosConfigUrl)
}

// randomID is the current boot ID
func (c *Config) getRandomId() (string, error) {
	b, err := ioutil.ReadFile(c.ProcBootId)
	if err != nil {
		glog.Errorf("fail to open %s: %q", c.ProcBootId, err)
		return "", err
	}
	randomId := string(b)
	randomId = strings.Trim(randomId, "\n")
	glog.V(4).Infof("RandomId: %q", randomId)
	return randomId, nil

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
			glog.V(4).Infof("uuid: %q", bootInfo.Uuid)
		}
		if strings.Contains(arg, macField) {
			bootInfo.Mac = strings.Split(arg, macField)[1]
			bootInfo.Mac = strings.Replace(bootInfo.Mac, "-", ":", -1)
			glog.V(4).Infof("mac: %q", bootInfo.Mac)
		}
	}
	bootInfo.RandomId, err = c.getRandomId()
	if err != nil {
		glog.Errorf("fail to get RandomId: %s", err)
		return bootInfo, err
	}
	return bootInfo, nil
}

func (c *Config) ParseCommandLine() (bootInfo BootInfo, err error) {
	b, err := ioutil.ReadFile(c.ProcCmdline)
	if err != nil {
		glog.Errorf("fail to read %s", err)
		return bootInfo, err
	}
	url, err := getCoreosConfigUrl(b)
	if err != nil {
		glog.Errorf("fail to get CoreOS Config Url %s", err)
		return bootInfo, err
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
					glog.V(4).Infof("Metadata uuid: %s", bootInfo.Uuid)
				} else if kv[0] == "mac" {
					bootInfo.Mac = strings.Replace(kv[1], "-", ":", -1)
					glog.V(4).Infof("Metadata mac: %s", bootInfo.Mac)
				}
			}
			bootInfo.RandomId, err = c.getRandomId()
			if err != nil {
				glog.Errorf("fail to get randomId: %s", err)
				return bootInfo, err
			}
			return bootInfo, nil
		}
	}
	msg := "Cannot find REQUEST_RAW_QUERY in metadata file"
	glog.Errorf(msg)
	return bootInfo, fmt.Errorf(msg)
}

func (c *Config) ParseMetadata() (bootInfo BootInfo, err error) {
	glog.V(4).Infof("Finding BootInfo from metadata file: %q", c.EnjoliverMetadata)
	b, err := ioutil.ReadFile(c.EnjoliverMetadata)
	if err != nil {
		glog.Errorf("fail to read %s: %s", c.EnjoliverMetadata, err)
		return bootInfo, err
	}
	return c.getBootInfoFromMetadata(b)
}
