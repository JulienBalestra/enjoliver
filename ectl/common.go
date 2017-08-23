package main

import (
	"encoding/json"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
)

const (
	EnjoliverConfigPath                 = "/configs"
	EnjoliverAgentPort                  = 8000
	SchedulerKubernetesControlPlanePath = "/scheduler/kubernetes-control-plane"
	SchedulerKubernetesNodePath         = "/scheduler/kubernetes-node"
	AsciiDisplay                        = "ascii"
	JsonDisplay                         = "json"
)

type Machine struct {
	Ipv4         string `json:"ipv4"`
	Fqdn         string `json:"fqdn"`
	Mac          string `json:"mac"`
	ControlPlane bool   `json:"control-plane"`
}

type Configuration struct {
	Clusters map[string][]string `structs:"clusters" mapstructure:"clusters"`
}

type Runtime struct {
	Config                 Configuration
	Cluster                string
	EndpointDisplay        EndpointDisplay
	ComponentStatusDisplay ComponentStatusDisplay
	Output                 string
	HideAsciiHeader        bool
}

type EnjoliverConfig struct {
	Fleet_etcd_client_port      int
	Vault_etcd_client_port      int
	Kubernetes_etcd_client_port int
	Kubernetes_api_server_port  int
	Vault_port                  int
}

func (r *Runtime) getEnjoliverConfig() (EnjoliverConfig, error) {
	var enjoliverConfig EnjoliverConfig
	b, err := r.SmartClient(EnjoliverConfigPath)
	if err != nil {
		glog.Errorf("fail to query: %s", err)
		return enjoliverConfig, err
	}
	err = json.Unmarshal(b, &enjoliverConfig)
	if err != nil {
		glog.Errorf("fail to unmarshal: %s", err)
		return enjoliverConfig, err
	}
	return enjoliverConfig, nil
}

func setAsciiTableStyleAndRender(asciiTable *tablewriter.Table) {
	asciiTable.SetRowSeparator(" ")
	asciiTable.SetColumnSeparator(" ")
	asciiTable.SetCenterSeparator("")
	asciiTable.Render()
}
