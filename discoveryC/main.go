package main

import (
	"log"
)


func main() {
	c, err := CreateConfig()
	if err != nil {
		log.Fatal(err)
		return
	}

	data, err := c.CollectData()
	if err != nil {
		log.Fatal(err)
	}

	err = c.PostToDiscovery(data)
	if err != nil {
		log.Fatal(err)
	}

	return
}
