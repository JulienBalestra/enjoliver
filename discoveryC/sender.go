package main

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
)

func PostToDiscovery(i interface{}) (err error) {
	b, _ := json.Marshal(&i)
	data := bytes.NewBuffer(b)
	log.Println(data)
	_, err = http.Post(CONF.DiscoveryAddress, "application/json", data)
	return
}
