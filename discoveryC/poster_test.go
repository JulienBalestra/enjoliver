package main

import (
	"testing"
	"net/http"
	"io/ioutil"
	"encoding/json"
)

func TestPostToDiscovery(t *testing.T) {
	var all []Iface
	i := Iface{
		IPv4:"192.168.1.1",
		CIDRv4:"192.168.1.1/24",
		Netmask:24,
		Name:"eth0",
		MAC:"00:00:00:00:00",
	}
	all = append(all, i)
	CONF.DiscoveryAddress = "http://127.0.0.1:8080"
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		var bodyBytes []byte
		bodyBytes, _ = ioutil.ReadAll(r.Body)
		var j []Iface
		json.Unmarshal(bodyBytes, &j)
		if len(j) != 1 && j[0] != i {
			t.Fail()
		}
	})
	go func() {
		e := http.ListenAndServe("127.0.0.1:8080", nil)
		if e != nil {
			t.Log(e)
			t.Fail()
		}
	}()
	err := PostToDiscovery(all)
	if err != nil {
		t.Fail()
	}
}

