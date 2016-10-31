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
	ifaces := LocalIfaces()
	err = PostToDiscovery(ifaces)
	if err != nil {
		log.Fatal(err)
	}
	return
}