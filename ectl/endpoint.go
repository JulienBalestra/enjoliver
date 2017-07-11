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

type KubernetesControlPlane struct {
	Ipv4 string `json:"ipv4"`
	Fqdn string `json:"fqdn"`
}

type EnjoliverConfig struct {
	Fleet_etcd_client_port      int
	Vault_etcd_client_port      int
	Kubernetes_etcd_client_port int
	Kubernetes_api_server_port  int
}

func display(kubernetesControlPlanes []KubernetesControlPlane, config EnjoliverConfig) {
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"FQDN", "etcd-fleet", "etcd-vault", "etcd-kube", "vault", "insecure-kube-apiserver", "kube-apiserver"})
	for _, node := range kubernetesControlPlanes {
		table.Append([]string{
			node.Fqdn,
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Fleet_etcd_client_port),
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_etcd_client_port),
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Kubernetes_etcd_client_port),
			fmt.Sprintf("https://%s:%d", node.Ipv4, vaultPort),
			fmt.Sprintf("http://%s:%d", node.Ipv4, config.Kubernetes_api_server_port),
			fmt.Sprintf("https://%s:%d", node.Ipv4, kubernetesApiServerSecurePort),
		})
	}
	table.Render()
}

func (r *Runtime) EndpointList() error {
	var kubernetesControlPlanes []KubernetesControlPlane
	var enjoliverConfig EnjoliverConfig

	b, err := r.SmartClient(schedulerKubernetesControlPlanePath)
	if err != nil {
		return err
	}
	err = json.Unmarshal(b, &kubernetesControlPlanes)
	if err != nil {
		glog.Errorf("fail to unmarshal: %s", err)
		return err
	}

	b, err = r.SmartClient(enjoliverConfigPath)
	if err != nil {
		return err
	}
	err = json.Unmarshal(b, &enjoliverConfig)
	if err != nil {
		glog.Errorf("fail to unmarshal: %s", err)
		return err
	}
	display(kubernetesControlPlanes, enjoliverConfig)
	return nil
}
