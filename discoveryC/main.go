package main

import (
	"github.com/golang/glog"
	"flag"
)


func main() {
	glog.V(2).Infof("starting discovery Client")
	flag.Parse()

	c, err := CreateConfig()
	if err != nil {
		glog.Errorf("fail to create config: %s", err)
		return
	}

	data, err := c.CollectData()
	if err != nil {
		glog.Errorf("fail to collect data: %s", err)
		return
	}

	err = c.PostToDiscovery(data)
	if err != nil {
		glog.Errorf("fail to send data: %s", err)
	}
	return
}
