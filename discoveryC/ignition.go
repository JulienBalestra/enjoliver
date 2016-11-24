package main

import (
	"k8s.io/kubernetes/staging/src/k8s.io/client-go/_vendor/github.com/emicklei/go-restful/log"
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
