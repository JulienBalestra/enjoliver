package main

import (
	"encoding/json"
	"fmt"
	"github.com/fatih/color"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
	"os"
)

const (
	machineHealthzPath = "/healthz"
	enjoliverAgentPort = 8000
)

type ComponentHealthz struct {
	FleetEtcdClient             bool
	KubeletHealthz              bool
	KubernetesApiserverInsecure bool
	KubernetesEtcdClient        bool
	RktApi                      bool
	Vault                       bool
	VaultEtcdClient             bool
}

type EnjoliverAgentHealthz struct {
	LivenessStatus ComponentHealthz
	//Errors         map[string]map[string]string
	Fqdn string
}

func (r *Runtime) getComponentStatus() ([]EnjoliverAgentHealthz, error) {
	var enjoliverAgentHealthzList []EnjoliverAgentHealthz

	cpList, err := r.getSchedulerKubernetesControlPlane()
	if err != nil {
		glog.Errorf("fail to get Kubernetes Control planes: %s", err)
		return nil, err
	}

	for _, cp := range cpList {
		uri := fmt.Sprintf("http://%s:%d%s", cp.Ipv4, enjoliverAgentPort, machineHealthzPath)
		b, err := httpGetUnmarshal(uri)
		if err != nil {
			glog.Errorf("fail to fetch %s: %s", uri, err)
			continue
		}
		var healthz EnjoliverAgentHealthz
		err = json.Unmarshal(b, &healthz)
		if err != nil {
			glog.Errorf("fail to unmarshal response from %s: %s: %q", uri, string(b), err)
			continue
		}
		if cp.Fqdn == "" {
			cp.Fqdn = cp.Ipv4
			glog.Errorf("no Fqdn for %s: using IP as Fqdn", cp.Ipv4)
		}
		healthz.Fqdn = cp.Fqdn
		enjoliverAgentHealthzList = append(enjoliverAgentHealthzList, healthz)
	}
	return enjoliverAgentHealthzList, err
}

func getColor(status bool) string {
	if status == false {
		return color.RedString("false")
	}
	return color.GreenString("true")
}

func (r *Runtime) createRowForComponentStatus(node EnjoliverAgentHealthz) []string {
	row := []string{node.Fqdn}
	for _, elt := range []bool{
		node.LivenessStatus.FleetEtcdClient,
		node.LivenessStatus.KubeletHealthz,
		node.LivenessStatus.KubernetesApiserverInsecure,
		node.LivenessStatus.KubernetesEtcdClient,
		node.LivenessStatus.RktApi,
		node.LivenessStatus.Vault,
		node.LivenessStatus.VaultEtcdClient} {
		row = append(row, getColor(elt))
	}
	return row
}

func (r *Runtime) createHeaderForComponentStatus() []string {
	header := []string{"Fqdn", "fleet-etcd", "kubelet", "kube-apiserver", "kube-etcd", "rkt-api", "vault", "vault-etcd"}
	return header
}

func (r *Runtime) displayComponentStatus(componentStatus []EnjoliverAgentHealthz, config EnjoliverConfig) {
	if r.Output == "ascii" {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		asciiTable.SetHeader(r.createHeaderForComponentStatus())
		for _, node := range componentStatus {
			asciiTable.Append(r.createRowForComponentStatus(node))
		}
		asciiTable.Render()
		return
	}
	if r.Output == "json" {
		// TODO
		return
	}
	glog.Warning("unknown output format")
}

func (r *Runtime) DisplayComponentStatus() error {
	componentStatus, err := r.getComponentStatus()
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	r.displayComponentStatus(componentStatus, enjoliverConfig)
	return nil
}
