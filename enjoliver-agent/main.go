package main

import (
	"net/http"
	"github.com/golang/glog"
	"os"
	"fmt"
	"encoding/json"
	"flag"
)

func probeUrl(url string) (error) {
	resp, err := http.Get(url)
	if err != nil {
		glog.Errorf("fail to get %s: %s", url, err)
		return err
	}

	if resp.StatusCode != 200 {
		errMsg := fmt.Sprintf("fail to probe %s StatusCode != 200: %d", url, resp.StatusCode)
		glog.Errorf(errMsg)
		return fmt.Errorf(errMsg)
	}

	return nil
}

func (run *Runtime) probeHealthz() (map[string]bool, error) {
	var err error

	healthReport := make(map[string]bool)
	for _, p := range run.LivenessProbes {
		healthReport[p.Name] = false
		err = probeUrl(p.Url)
		if err != nil {
			glog.Errorf("fail to probe %s: %s", p.Name, err)
			continue
		}
		healthReport[p.Name] = true
	}

	return healthReport, nil
}

func (run *Runtime) handlerHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		health, err := run.probeHealthz()
		if err != nil {
			glog.Errorf("fail to get health status: %s", err)
			return
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

type Runtime struct {
	LivenessProbes []LivenessProbe
}

func main() {
	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	glog.V(2).Infof("starting node-agent")
	p, err := getLivenessProbesToQuery()
	if err != nil {
		glog.Errorf("fail to get LivenessProbes to query: %s", err)
		os.Exit(2)
	}

	run := &Runtime{p}
	http.HandleFunc("/healthz", run.handlerHealthz)
	glog.Fatal(http.ListenAndServe("0.0.0.0:8000", nil))
}
