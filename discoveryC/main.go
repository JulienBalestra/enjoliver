package main

import (
	"log"
)

var CONF, _ = CreateConfig()

func main() {
	log.Println(LocalIfaces())

	return
}