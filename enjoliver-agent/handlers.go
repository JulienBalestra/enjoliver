package main

import (
	"encoding/json"
	"github.com/golang/glog"
	"io/ioutil"
	"net/http"
)

func (run *Runtime) handlerHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
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
	if r.Method == http.MethodGet {
		binaries := GetComponentVersion()
		if len(binaries.Errors) != 0 {
			glog.Errorf("fail to get health status for: %s", binaries.Errors)
			w.WriteHeader(503)
		}
		writeResponse(w, &binaries)
	}
}

// [ img1, img2, img3 ]
func (run *Runtime) handlerHackRktFetch(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		var b []byte
		var images []string

		b, err := ioutil.ReadAll(r.Body)
		if err != nil {
			glog.Errorf("fail to read body: %s", err)
			w.WriteHeader(400)
			return
		}
		err = json.Unmarshal(b, &images)
		if err != nil {
			glog.Errorf("fail to unmarshal body %q: %s", string(b), err)
			w.WriteHeader(400)
			return
		}
		errList := run.RktFetch(images)
		if len(errList) > 0 {
			glog.Errorf("fail to proceed to request: %s", errList)
			w.WriteHeader(500)
			var errListStr []string
			for _, elt := range errList {
				errListStr = append(errListStr, elt.Error())
			}
			b, err := json.Marshal(&errListStr)
			if err != nil {
				glog.Errorf("fail to marshal error list: %s", err)
				return
			}
			w.Write(b)
		}
		return
	}
	w.WriteHeader(405)
}

func (run *Runtime) handlerHackSystemdRestartKubernetesStack(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		err := run.RestartKubernetes()
		if err != nil {
			glog.Errorf("fail to proceed: %s", err)
			w.WriteHeader(500)
		}
		return
	}
	w.WriteHeader(405)
}
