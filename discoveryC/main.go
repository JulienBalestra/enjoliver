package main

import (
	"log"
)

var CONF Config

func main() {
	var err error
	CONF, err = CreateConfig()
	if err != nil {
		log.Fatal(err)
		return
	}
	data := CollectData()
	err = PostToDiscovery(data)
	if err != nil {
		log.Fatal(err)
	}
	return
}
