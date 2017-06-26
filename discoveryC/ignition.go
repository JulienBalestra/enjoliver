package main

import (
	"io/ioutil"
	"log"
	"strings"
)

func (c *Config) GetIgnitionJournal() (filterLines []string, err error) {
	content, e := ioutil.ReadFile(c.IgnitionFile)
	var lines []string

	if e != nil {
		log.Print(e)
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
	return filterLines, nil
}
