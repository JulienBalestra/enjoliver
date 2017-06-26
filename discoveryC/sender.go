package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
)

func (c *Config) PostToDiscovery(i interface{}) (err error) {
	b, err := json.Marshal(&i)
	if err != nil {
		return err
	}
	data := bytes.NewBuffer(b)
	log.Println(data)
	_, err = http.Post(c.DiscoveryAddress, "application/json", data)
	return err
}
