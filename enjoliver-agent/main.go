package main

import (
	"flag"
	"github.com/golang/glog"
	"net/http"
	"os"
	"time"
)

const (
	ControlPlaneFlagName = "control-plane"
	RktFetchInsecure     = "rkt-fetch-insecure"
)

type Runtime struct {
	HttpLivenessProbes []HttpLivenessProbe
}

func main() {
	glog.Infof("starting node-agent")
	flag.Bool(ControlPlaneFlagName, false, "Is control-plane node")
	flag.Bool(RktFetchInsecure, true, "rkt fetch --insecure-options=all")

	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	p, err := getHttpLivenessProbesToQuery()
	if err != nil {
		glog.Errorf("fail to get HttpLivenessProbes to query: %s", err)
		os.Exit(2)
	}

	run := &Runtime{p}
	http.DefaultClient.Timeout = time.Second
	http.HandleFunc("/healthz", run.handlerHealthz)
	http.HandleFunc("/version", run.handlerVersion)
	http.HandleFunc("/hack/rkt/fetch", run.handlerHackRktFetch)
	http.HandleFunc("/hack/systemd/restart/kubernetes", run.handlerHackSystemdRestartKubernetesStack)
	glog.Fatal(http.ListenAndServe("0.0.0.0:8000", nil))
}
