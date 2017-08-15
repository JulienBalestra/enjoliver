package main

import (
	"flag"
	"fmt"
	"github.com/golang/glog"
	"os"
	"strconv"
	"strings"
)

const (
	etcdLivenessPath       = "/health"
	kubernetesLivenessPath = "/healthz"
	vaultLivenessPath      = "/v1/sys/health"
)

func getPortFromEnv(key string) (int, error) {
	port, err := strconv.Atoi(os.Getenv(key))
	if err != nil {
		glog.Warningf("cannot get from envName %s: %s", key, err)
		return port, err
	}
	return port, nil
}

type HttpLivenessProbe struct {
	Name string
	Path string
	Port int
	Url  string
}

func formatProbeName(envPortName string) string {
	str := strings.ToLower(envPortName)
	str = strings.Replace(str, "port", "", 1)
	strLowerList := strings.Split(str, "_")
	var strCapitalizeList []string
	for _, s := range strLowerList {
		strCapitalizeList = append(strCapitalizeList, strings.Title(s))
	}

	return strings.Join(strCapitalizeList, "")
}

func constructLivenessProbe(envPortName string, path string) (HttpLivenessProbe, error) {
	var probe HttpLivenessProbe
	var err error

	probe.Port, err = getPortFromEnv(envPortName)
	if err != nil {
		glog.Errorf("fail to get environment variable %s: %s", envPortName, err)
		return probe, err
	}

	probe.Name = formatProbeName(envPortName)
	probe.Path = path
	probe.Url = fmt.Sprintf("http://127.0.0.1:%d%s", probe.Port, probe.Path)
	return probe, nil
}

func getHttpLivenessProbesToQuery() ([]HttpLivenessProbe, error) {
	var livenessProbes []HttpLivenessProbe

	probes := [][]string{
		{"FLEET_ETCD_CLIENT_PORT", etcdLivenessPath},
		{"KUBERNETES_ETCD_CLIENT_PORT", etcdLivenessPath},
		{"VAULT_ETCD_CLIENT_PORT", etcdLivenessPath},
		{"KUBERNETES_APISERVER_INSECURE_PORT", kubernetesLivenessPath},
		{"KUBELET_HEALTHZ_PORT", kubernetesLivenessPath},
	}
	if flag.Lookup(vaultFlagName).Value.String() == "true" {
		glog.V(4).Infof("flag %s set to true", vaultFlagName)
		probes = append(probes, []string{"VAULT_PORT", vaultLivenessPath})
	}

	for _, elt := range probes {
		probe, err := constructLivenessProbe(elt[0], elt[1])
		if err != nil {
			glog.Errorf("fail to aggregate probes: %s", err)
			return livenessProbes, err
		}
		livenessProbes = append(livenessProbes, probe)
	}

	return livenessProbes, nil
}
