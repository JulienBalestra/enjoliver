package main

import (
	"log"
	"io/ioutil"
	"strings"
)

var (
	prefixSkips = []string{"Ignition", "parsing config:"}
)

func GetIgnitionJournal() []string {
	content, e := ioutil.ReadFile(CONF.IgnitionFile)
	var lines []string
	var filter_lines []string

	if e != nil {
		log.Print(e)
		return lines
	}
	lines = strings.Split(string(content), "\n")

	var skip bool
	for _, line := range lines {
		skip = false
		if len(line) == 0 {
			// skip == true: useless to iterate over an empty string
			continue
		}
		for _, prefix := range prefixSkips {
			if strings.HasPrefix(line, prefix) {
				skip = true
			}
		}
		if skip == false {
			filter_lines = append(filter_lines, line)
		}
	}
	return filter_lines
}
