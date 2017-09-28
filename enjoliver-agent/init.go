package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/golang/glog"
)

const (
	etcdLivenessPath         = "/health"
	kubernetesLivenessPath   = "/healthz"
	vaultLivenessPath        = "/v1/sys/health"
	locksmithEtcd            = "FleetEtcdClient"
	locksmithRawQueryEnvName = "REQUEST_RAW_QUERY"
	locksmithSuffix          = "EnjoliverAgent"
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
	Name     string
	Path     string
	Port     int
	Url      string
	Endpoint string
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
	probe.Endpoint = fmt.Sprintf("http://127.0.0.1:%d", probe.Port)
	probe.Url = fmt.Sprintf("%s%s", probe.Endpoint, probe.Path)
	return probe, nil
}

func getHttpLivenessProbesToQuery() ([]HttpLivenessProbe, error) {
	var livenessProbes []HttpLivenessProbe

	probes := [][]string{
		{"FLEET_ETCD_CLIENT_PORT", etcdLivenessPath},
		{"KUBELET_HEALTHZ_PORT", kubernetesLivenessPath},
	}
	if flag.Lookup(ControlPlaneFlagName).Value.String() == "true" {
		glog.V(4).Infof("flag %s set to true", ControlPlaneFlagName)
		probes = append(probes, [][]string{
			{"VAULT_PORT", vaultLivenessPath},
			{"VAULT_ETCD_CLIENT_PORT", etcdLivenessPath},
			{"KUBERNETES_ETCD_CLIENT_PORT", etcdLivenessPath},
			{"KUBERNETES_APISERVER_INSECURE_PORT", kubernetesLivenessPath},
		}...)
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

// from environment file (/etc/metadata.env) get the RAW QUERY
func getLocksmithConfig(livenessProbes []HttpLivenessProbe) (string, string, error) {
	rawQuery := os.Getenv(locksmithRawQueryEnvName)
	if rawQuery == "" {
		errMsg := fmt.Sprintf("fail to get ENV: %s", locksmithRawQueryEnvName)
		glog.Errorf(errMsg)
		return "", "", fmt.Errorf(errMsg)
	}
	// add a suffix to the raw query to avoid unlocking by lifecycle process
	rawQuery = fmt.Sprintf("%s-%s", rawQuery, locksmithSuffix)

	for _, p := range livenessProbes {
		if p.Name == locksmithEtcd {
			glog.V(4).Infof("locksmith endpoint %s is %s", locksmithEtcd, p.Endpoint)
			return p.Endpoint, rawQuery, nil
		}
	}

	errMsg := fmt.Sprintf("fail to find locksmith endpoint %s in probes", locksmithEtcd)
	glog.Errorf(errMsg)
	return "", "", fmt.Errorf(errMsg)
}
