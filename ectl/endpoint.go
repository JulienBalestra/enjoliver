package main

import (
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
	"os"
)

const (
	kubernetesApiServerSecurePort = 6443
)

type EndpointDisplay struct {
	Fleet      bool
	Vault      bool
	Kubernetes bool
}

func (r *Runtime) createHeaderForEndpoint() []string {
	header := []string{"Fqdn"}
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

func (r *Runtime) createRowForEndpoint(node SchedulerKubernetesControlPlane, config EnjoliverConfig) []string {
	if node.Fqdn == "" {
		node.Fqdn = node.Ipv4
		glog.Errorf("no Fqdn for %s: using IP as Fqdn", node.Ipv4)
	}
	row := []string{node.Fqdn}
	if r.EndpointDisplay.Fleet {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Fleet_etcd_client_port))
	}
	if r.EndpointDisplay.Kubernetes {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, kubernetesApiServerSecurePort))
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Kubernetes_etcd_client_port))
	}
	if r.EndpointDisplay.Vault {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_port))
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_etcd_client_port))
	}
	return row
}

func (r *Runtime) displayEndpoints(kubernetesControlPlanes []SchedulerKubernetesControlPlane, config EnjoliverConfig) {
	if r.Output == "ascii" {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		asciiTable.SetHeader(r.createHeaderForEndpoint())
		for _, node := range kubernetesControlPlanes {
			asciiTable.Append(r.createRowForEndpoint(node, config))
		}
		asciiTable.Render()
		return
	}
	if r.Output == "json" {
		// TODO use a struct to make a json more exploitable
		var stringArray [][]string
		for _, node := range kubernetesControlPlanes {
			stringArray = append(stringArray, r.createRowForEndpoint(node, config))
		}
		b, err := json.Marshal(stringArray)
		if err != nil {
			glog.Errorf("fail to marshal: %s", err)
			return
		}
		os.Stdout.Write(b)
		return
	}
	glog.Warning("unknown output format")
}

func (r *Runtime) getSchedulerKubernetesControlPlane() ([]SchedulerKubernetesControlPlane, error) {
	var schedulerKubeControlPlane []SchedulerKubernetesControlPlane

	b, err := r.SmartClient(SchedulerKubernetesControlPlanePath)
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

func (r *Runtime) DisplayEndpoints() error {
	schedulerKubeControlPlane, err := r.getSchedulerKubernetesControlPlane()
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	r.displayEndpoints(schedulerKubeControlPlane, enjoliverConfig)
	return nil
}
