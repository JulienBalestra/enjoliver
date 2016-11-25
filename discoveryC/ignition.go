package main

import (
	"log"
	"io/ioutil"
	"strings"
)

func GetIgnitionJournal() []string {
	content, e := ioutil.ReadFile(CONF.IgnitionFile)
	var lines []string
	if e != nil {
		log.Print(e)
		return lines
	}
	lines = strings.Split(string(content), "\n")
	return lines
}
