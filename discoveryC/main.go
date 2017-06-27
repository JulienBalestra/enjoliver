package main

import (
	"flag"
	"github.com/golang/glog"
)

func main() {
	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	glog.V(2).Infof("starting discovery Client")

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
	glog.Flush()
	return
}
