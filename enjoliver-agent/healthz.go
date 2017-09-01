package main

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/golang/glog"
	rktapi "github.com/rkt/rkt/api/v1alpha"
	"google.golang.org/grpc"
)

const (
	defaultRktAPIServiceAddr = "localhost:15441"
	timeout                  = 1 * time.Second
)

type ProbeStatus struct {
	Name    string
	Healthy bool
	Error   error
}

type probeRunner struct {
	probeResultCh chan ProbeStatus
	wg            sync.WaitGroup
}

type AllProbesStatus struct {
	LivenessStatus map[string]bool
	Errors         map[string]string
}

func queryHttpLivenessProbe(probe HttpLivenessProbe, ch chan ProbeStatus) {
	var probeResult ProbeStatus

	probeResult.Name = probe.Name
	resp, err := http.Get(probe.Url)
	glog.V(4).Infof("GET %s done", probe.Url)
	if err != nil {
		probeResult.Error = fmt.Errorf("fail to get %s: %s", probe.Url, err)
		glog.Errorf(probeResult.Error.Error())
	} else if resp.StatusCode != 200 {
		probeResult.Error = fmt.Errorf("fail to probe %s StatusCode != 200 -> %d", probe.Url, resp.StatusCode)
		glog.Errorf(probeResult.Error.Error())
	} else {
		probeResult.Healthy = true
	}
	ch <- probeResult
	glog.V(2).Infof("%s at %s Healthy: %t", probe.Name, probe.Url, probeResult.Healthy)
}

func probeRktApi(ch chan ProbeStatus) {
	var probeResult ProbeStatus
	defer func() { ch <- probeResult }()

	probeResult.Name = "RktApi"

	ctx, _ := context.WithTimeout(context.Background(), timeout)
	conn, err := grpc.DialContext(ctx, defaultRktAPIServiceAddr, grpc.WithInsecure())
	if err != nil {
		probeResult.Error = err
		glog.Errorf(probeResult.Error.Error())
		return
	}
	defer func() {
		time.AfterFunc(time.Millisecond*100, func() {
			err := conn.Close()
			if err != nil {
				glog.Warningf("gRPC connection closed with err: %q", err)
			}
		})
	}()

	rktApi := rktapi.NewPublicAPIClient(conn)
	_, err = rktApi.GetInfo(context.Background(), &rktapi.GetInfoRequest{})
	if err != nil {
		probeResult.Error = err
		glog.Errorf(probeResult.Error.Error())
		return
	}
	probeResult.Healthy = true
	glog.V(2).Infof("%s at %s Healthy: %t", probeResult.Name, defaultRktAPIServiceAddr, probeResult.Healthy)
}

func (run *Runtime) GetComponentStatus() AllProbesStatus {
	var allProbes AllProbesStatus
	allProbes.LivenessStatus = make(map[string]bool)
	allProbes.Errors = make(map[string]string)

	ch := make(chan ProbeStatus)
	defer close(ch)
	for _, probe := range run.HttpLivenessProbes {
		glog.V(3).Infof("ask for query %s", probe.Url)
		go queryHttpLivenessProbe(probe, ch)
	}
	go probeRktApi(ch)

	glog.V(3).Infof("all queries sent")
	for i := 0; i < len(run.HttpLivenessProbes)+1; i++ {
		probeResult := <-ch
		glog.V(3).Infof("received %s: %t", probeResult.Name, probeResult.Healthy)
		allProbes.LivenessStatus[probeResult.Name] = probeResult.Healthy
		if probeResult.Error != nil {
			allProbes.Errors[probeResult.Name] = probeResult.Error.Error()
		}
	}
	return allProbes
}
