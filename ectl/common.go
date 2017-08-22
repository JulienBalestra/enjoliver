package main

import (
	"github.com/golang/glog"
	"encoding/json"
)

const (
	enjoliverConfigPath                 = "/configs"
	SchedulerKubernetesControlPlanePath = "/scheduler/kubernetes-control-plane"
	SchedulerKubernetesNodePath         = "/scheduler/kubernetes-node"
)

type SchedulerKubernetesControlPlane struct {
	Ipv4 string `json:"ipv4"`
	Fqdn string `json:"fqdn"`
	Mac  string `json:"mac"`
}

type Configuration struct {
	Clusters map[string][]string `structs:"clusters" mapstructure:"clusters"`
}

type Runtime struct {
	Config          Configuration
	Cluster         string
	EndpointDisplay EndpointDisplay
	Output          string
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
	b, err := r.SmartClient(enjoliverConfigPath)
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
