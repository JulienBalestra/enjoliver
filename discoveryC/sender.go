package main

import (
	"bytes"
	"encoding/json"
	"github.com/golang/glog"
	"net/http"
)

func (c *Config) PostToDiscovery(i interface{}) (err error) {
	b, err := json.Marshal(&i)
	if err != nil {
		glog.Errorf("fail to marshal: %s", err)
		return err
	}
	data := bytes.NewBuffer(b)
	glog.V(2).Infof("Data to send: %q", data)
	_, err = http.Post(c.DiscoveryAddress, "application/json", data)
	if err != nil {
		glog.Errorf("fail to send data to %s", c.DiscoveryAddress)
	}
	return err
}
