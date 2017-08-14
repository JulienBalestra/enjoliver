package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/golang/glog"
	"net/http"
	"os"
	"sync"
	"time"
)

const (
	vaultFlagName = "vault"
)

type ProbeStatus struct {
	Name    string
	Healthy bool
	Error   string
}

type probeRunner struct {
	probeResultCh chan ProbeStatus
	wg            sync.WaitGroup
}

func queryLivenessProbe(probe LivenessProbe, ch chan ProbeStatus) {
	var probeResult ProbeStatus

	probeResult.Name = probe.Name
	http.DefaultClient.Timeout = time.Second
	resp, err := http.Get(probe.Url)
	glog.V(4).Infof("GET %s done", probe.Url)
	if err != nil {
		probeResult.Error = fmt.Sprintf("fail to get %s: %s", probe.Url, err)
		glog.Errorf(probeResult.Error)
	} else if resp.StatusCode != 200 {
		probeResult.Error = fmt.Sprintf("fail to probe %s StatusCode != 200 -> %d", probe.Url, resp.StatusCode)
		glog.Errorf(probeResult.Error)
	} else {
		probeResult.Healthy = true
	}
	ch <- probeResult
	glog.V(2).Infof("%s at %s Healthy: %t", probe.Name, probe.Url, probeResult.Healthy)
}

func (run *Runtime) runProbes() AllProbesStatus {
	var allProbes AllProbesStatus
	allProbes.LivenessStatus = make(map[string]bool)
	allProbes.Errors = make(map[string]string)

	ch := make(chan ProbeStatus)
	defer close(ch)
	for _, probe := range run.LivenessProbes {
		glog.V(3).Infof("ask for query %s", probe.Url)
		go queryLivenessProbe(probe, ch)
	}

	glog.V(3).Infof("all queries sent")
	for range run.LivenessProbes {
		probeResult := <-ch
		glog.V(3).Infof("received %s: %t", probeResult.Name, probeResult.Healthy)
		allProbes.LivenessStatus[probeResult.Name] = probeResult.Healthy
		if probeResult.Error != "" {
			allProbes.Errors[probeResult.Name] = probeResult.Error
		}
	}
	return allProbes
}

type AllProbesStatus struct {
	LivenessStatus map[string]bool
	Errors         map[string]string
}

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

type Runtime struct {
	LivenessProbes []LivenessProbe
}

func main() {
	flag.Bool(vaultFlagName, false, "Enable vault probe")

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
