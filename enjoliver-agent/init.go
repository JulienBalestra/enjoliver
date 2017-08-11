package main

import (
	"os"
	"github.com/golang/glog"
	"strconv"
)

type EnjoliverConfig struct {
	FleetEtcdClientPort      int
	KubernetesEtcdClientPort int
	VaultEtcdClientPort      int

	KubeletPort              int
	KubernetesApiServerPort  int
	VaultPort                int
}

func getConfig() (EnjoliverConfig, error) {
	var ec EnjoliverConfig
	var err error

	ec.FleetEtcdClientPort, err = strconv.Atoi(os.Getenv("FLEET_ETCD_CLIENT_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env FLEET_ETCD_CLIENT_PORT: %s", err)
		return ec, err
	}

	ec.VaultEtcdClientPort, err = strconv.Atoi(os.Getenv("VAULT_ETCD_CLIENT_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env VAULT_ETCD_CLIENT_PORT: %s", err)
		return ec, err
	}

	ec.KubernetesEtcdClientPort, err = strconv.Atoi(os.Getenv("KUBERNETES_ETCD_CLIENT_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env KUBERNETES_ETCD_CLIENT_PORT: %s", err)
		return ec, err
	}

	ec.KubernetesApiServerPort, err = strconv.Atoi(os.Getenv("KUBERNETES_API_SERVER_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env KUBERNETES_API_SERVER_PORT: %s", err)
		return ec, err
	}

	ec.KubeletPort, err = strconv.Atoi(os.Getenv("KUBELET_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env KUBELET_PORT: %s", err)
		return ec, err
	}

	ec.VaultPort, err = strconv.Atoi(os.Getenv("VAULT_PORT"))
	if err != nil {
		glog.Errorf("cannot get from env VAULT_PORT: %s", err)
		return ec, err
	}

	return ec, nil
}
