package main

import (
	"github.com/golang/glog"
	"io/ioutil"
	"strings"
)

func (c *Config) GetIgnitionJournal() (filterLines []string, err error) {
	var lines []string

	content, e := ioutil.ReadFile(c.IgnitionFile)
	if e != nil {
		glog.Errorf("fail to read %s: %s", c.IgnitionFile, err)
		return lines, err
	}
	lines = strings.Split(string(content), "\n")

	for _, line := range lines {
		if len(line) == 0 {
			// skip == true: useless to iterate over an empty string
			continue
		}
		filterLines = append(filterLines, line)
	}
	glog.V(2).Infof("ignition journal have %d lines", len(filterLines))
	return filterLines, nil
}
