package main

import (
	"encoding/json"
	"github.com/golang/glog"
	"net/http"
)

func (run *Runtime) handlerHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		health := run.GetComponentStatus()
		if len(health.Errors) != 0 {
			glog.Errorf("fail to get health status for: %s", health.Errors)
			w.WriteHeader(503)
		}
		writeResponse(w, &health)
	}
}

func writeResponse(w http.ResponseWriter, v interface{}) {
	b, err := json.Marshal(&v)
	if err != nil {
		glog.Errorf("fail to marshal health: %s", err)
		return
	}

	_, err = w.Write(b)
	if err != nil {
		glog.Errorf("fail to write %s on response: %s", string(b), err)
	}

}

func (run *Runtime) handlerVersion(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		binaries := GetComponentVersions()
		if len(binaries.Errors) != 0 {
			glog.Errorf("fail to get health status for: %s", binaries.Errors)
			w.WriteHeader(503)
		}
		writeResponse(w, &binaries)
	}
}
