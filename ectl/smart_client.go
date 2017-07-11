package main

import (
	"fmt"
	"github.com/golang/glog"
	"io/ioutil"
	"net/http"
)

// Iter on each URI to apply the func
func (r *Runtime) SmartClient(path string) ([]byte, error) {
	uris := r.Config.Clusters[r.Cluster]
	for _, uri := range uris {
		url := fmt.Sprintf("%s/%s", uri, path)
		glog.V(2).Infof("GET %s", url)
		resp, err := http.Get(url)
		if err != nil {
			glog.Warningf("fail GET %s: %s %d", url, err)
			continue
		}
		b, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			glog.Errorf("fail to read body: %s", err)
			return nil, err
		}
		resp.Body.Close()
		return b, err
	}
	return nil, fmt.Errorf("fail to run SmartClient against cluster %q %d URI %s with %q", r.Cluster, len(uris), uris, path)
}
