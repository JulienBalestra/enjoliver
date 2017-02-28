package main

import (
	"io/ioutil"
	"log"
	"strings"
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

	for _, line := range lines {
		if len(line) == 0 {
			// skip == true: useless to iterate over an empty string
			continue
		}
		filter_lines = append(filter_lines, line)
	}
	return filter_lines
}
