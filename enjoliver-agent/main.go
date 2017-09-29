package main

import (
	"flag"
	"github.com/golang/glog"
	"net/http"
	"os"
	"sync"
	"time"
)

const (
	ControlPlaneFlagName = "control-plane"
	RktFetchInsecure     = "rkt-fetch-insecure"
)

type Runtime struct {
	HttpLivenessProbes     []HttpLivenessProbe
	LocksmithEndpoint      string
	LocksmithLock          string
	RestartKubernetesLock  sync.RWMutex
	KubernetesSystemdUnits []string
}

func main() {
	glog.Infof("starting node-agent")
	flag.Bool(ControlPlaneFlagName, false, "Is control-plane node")
	flag.Bool(RktFetchInsecure, true, "rkt fetch --insecure-options=all")

	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	controlPlane := false
	if flag.Lookup(ControlPlaneFlagName).Value.String() == "true" {
		controlPlane = true
		glog.Infof("node-agent is in control-plane mode")
	}

	p, err := getHttpLivenessProbesToQuery(controlPlane)
	if err != nil {
		glog.Errorf("fail to get HttpLivenessProbes to query: %s", err)
		os.Exit(2)
	}

	locksmithEndpoint, locksmithLockName, err := getLocksmithConfig(p)
	if err != nil {
		glog.Errorf("fail to get locksmith endpoint in probes: %s", err)
		os.Exit(3)
	}

	run := &Runtime{
		p,
		locksmithEndpoint,
		locksmithLockName,
		sync.RWMutex{},
		getKubernetesSystemdUnits(controlPlane),
	}
	http.DefaultClient.Timeout = time.Second * 2
	http.HandleFunc("/", run.handlerRoot)
	http.HandleFunc(RouteHealthz, run.handlerHealthz)
	http.HandleFunc(RouteVersion, run.handlerVersion)
	http.HandleFunc(RouteHackRktFetch, run.handlerHackRktFetch)
	http.HandleFunc(RouteHackSystemdRestartKubernetes, run.handlerHackSystemdRestartKubernetesStack)
	glog.Fatal(http.ListenAndServe("0.0.0.0:8000", nil))
}
