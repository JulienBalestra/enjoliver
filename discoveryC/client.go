package main

import (
	"encoding/json"
	"net/http"
	"bytes"
	"log"
)

func PostToDiscovery(ifaces []Iface) (err error) {
	b, _ := json.Marshal(&ifaces)
	data := bytes.NewBuffer(b)
	log.Println(data)
	_, err = http.Post(CONF.DiscoveryAddress, "application/json", data)
	return
}
