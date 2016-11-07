package main

import (
	"encoding/json"
	"net/http"
	"bytes"
	"log"
)

func PostToDiscovery(i interface{}) (err error) {
	b, _ := json.Marshal(&i)
	data := bytes.NewBuffer(b)
	log.Println(data)
	_, err = http.Post(CONF.DiscoveryAddress, "application/json", data)
	return
}
