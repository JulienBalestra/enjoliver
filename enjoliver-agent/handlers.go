package main

import (
	"encoding/json"
	"github.com/golang/glog"
	"net/http"
)

func (run *Runtime) handlerHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		health := run.runProbes()
		if len(health.Errors) != 0 {
			glog.Errorf("fail to get health status for: %s", health.Errors)
			w.WriteHeader(503)
		}

		b, err := json.Marshal(&health)
		if err != nil {
			glog.Errorf("fail to marshal health: %s", err)
			return
		}

		_, err = w.Write(b)
		if err != nil {
			glog.Errorf("fail to write %s on response: %s", string(b), err)
		}
	}
}
