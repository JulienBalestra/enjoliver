package main

import (
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
	"os"
)

const (
	schedulerKubernetesControlPlanePath = "/scheduler/kubernetes-control-plane"
	enjoliverConfigPath                 = "/configs"
	vaultPort                           = 8200
	kubernetesApiServerSecurePort       = 6443
)

type EndpointDisplay struct {
	Fleet      bool
	Vault      bool
	Kubernetes bool
}

type SchedulerKubernetesControlPlane struct {
	Ipv4 string `json:"ipv4"`
	Fqdn string `json:"fqdn"`
	Mac  string `json:"mac"`
}

type EnjoliverConfig struct {
	Fleet_etcd_client_port      int
	Vault_etcd_client_port      int
	Kubernetes_etcd_client_port int
	Kubernetes_api_server_port  int
}

func (r *Runtime) createHeader() []string {
	header := []string{"FQDN"}
	if r.EndpointDisplay.Fleet {
		header = append(header, "etcd-fleet")
	}
	if r.EndpointDisplay.Kubernetes {
		header = append(header, "kube-apiserver")
		header = append(header, "etcd-kube")
	}
	if r.EndpointDisplay.Vault {
		header = append(header, "vault")
		header = append(header, "etcd-vault")
	}
	return header
}

func (r *Runtime) createRow(node SchedulerKubernetesControlPlane, config EnjoliverConfig) []string {
	row := []string{node.Fqdn}
	if r.EndpointDisplay.Fleet {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Fleet_etcd_client_port))
	}
	if r.EndpointDisplay.Kubernetes {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, kubernetesApiServerSecurePort))
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Kubernetes_etcd_client_port))
	}
	if r.EndpointDisplay.Vault {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, vaultPort))
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_etcd_client_port))
	}
	return row
}

func (r *Runtime) display(kubernetesControlPlanes []SchedulerKubernetesControlPlane, config EnjoliverConfig) {
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader(r.createHeader())
	for _, node := range kubernetesControlPlanes {
		table.Append(r.createRow(node, config))
	}
	table.Render()
}

func (r *Runtime) getSchedulerKubernetesControlPlane() ([]SchedulerKubernetesControlPlane, error) {
	var schedulerKubeControlPlane []SchedulerKubernetesControlPlane

	b, err := r.SmartClient(schedulerKubernetesControlPlanePath)
	if err != nil {
		return nil, err
	}
	err = json.Unmarshal(b, &schedulerKubeControlPlane)
	if err != nil {
		glog.Errorf("fail to unmarshal: %s", err)
		return nil, err
	}
	return schedulerKubeControlPlane, nil
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

func (r *Runtime) DisplayEndpoints() error {
	schedulerKubeControlPlane, err := r.getSchedulerKubernetesControlPlane()
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	r.display(schedulerKubeControlPlane, enjoliverConfig)
	return nil
}
