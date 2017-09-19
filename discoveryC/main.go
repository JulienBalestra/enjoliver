package main

import (
	"flag"
	"github.com/golang/glog"
	"os"
)

func main() {
	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	glog.V(2).Infof("starting discovery Client")

	c, err := CreateConfig()
	if err != nil {
		glog.Errorf("fail to create config: %s", err)
		os.Exit(1)
		return
	}

	data, err := c.CollectData()
	if err != nil {
		glog.Errorf("fail to collect data: %s", err)
		os.Exit(2)
		return
	}

	err = c.PostToDiscovery(data)
	if err != nil {
		glog.Errorf("fail to send data: %s", err)
		os.Exit(3)
	}
	glog.Flush()
	return
}
