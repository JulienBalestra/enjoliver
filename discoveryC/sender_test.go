package main

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"testing"
	"time"
)

func TestPostToDiscovery(t *testing.T) {
	var data DiscoveryData

	c, err := CreateConfig()
	if err != nil {
		t.Error(err)
	}
	i := Iface{
		IPv4:    "192.168.1.1",
		CIDRv4:  "192.168.1.1/24",
		Netmask: 24,
		Name:    "eth0",
		MAC:     "00:00:00:00:00",
	}
	data.Interfaces = append(data.Interfaces, i)

	data.BootInfo.Mac = "00:00:00:00:00"
	data.BootInfo.Uuid = "2023e709-39b4-47d7-8905-e8be3e6bc2c6"
	data.LLDPInfo.IsFile = true
	data.LLDPInfo.Data.Interfaces = []XInterface{}

	c.DiscoveryAddress = "http://127.0.0.1:8888"
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		var bodyBytes []byte
		bodyBytes, _ = ioutil.ReadAll(r.Body)
		var rcvData DiscoveryData

		err := json.Unmarshal(bodyBytes, &rcvData)
		if err != nil {
			t.Error(err)
		}
	})
	go func() {
		e := http.ListenAndServe("127.0.0.1:8888", nil)
		if e != nil {
			t.Log(e)
			t.Fail()
		}
	}()
	// wait or not the http server go routine
	for i := 0; i < 10; i++ {
		err := c.PostToDiscovery(data)
		if err == nil {
			break
		} else {
			t.Log(err)
			time.Sleep(100 * time.Millisecond)
		}
	}
	if err != nil {
		t.Log(err)
		t.Fail()
	}
}
