package main

import (
	"flag"
	"github.com/golang/glog"
	"net/http"
	"os"
	"time"
)

const (
	vaultFlagName = "vault"
)

type Runtime struct {
	HttpLivenessProbes []HttpLivenessProbe
}

func main() {
	glog.V(2).Infof("starting node-agent")
	flag.Bool(vaultFlagName, false, "Enable vault probe")

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
	glog.Fatal(http.ListenAndServe("0.0.0.0:8000", nil))
}
