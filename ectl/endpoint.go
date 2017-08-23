package main

import (
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
	"os"
	"sort"
)

const (
	KubernetesApiServerSecurePort = 6443
)

type EndpointDisplay struct {
	Fleet, Vault, Kubernetes bool
}

func (r *Runtime) createHeaderForEndpoint() []string {
	header := []string{"Fqdn"}
	if r.EndpointDisplay.Fleet {
		header = append(header, "etcd-fleet")
	}
	if r.EndpointDisplay.Kubernetes {
		header = append(header, []string{"kube-apiserver", "etcd-kube"}...)
	}
	if r.EndpointDisplay.Vault {
		header = append(header, []string{"vault", "etcd-vault"}...)
	}
	return header
}

func (r *Runtime) createRowForEndpoint(node Machine, config EnjoliverConfig) []string {
	if node.Fqdn == "" {
		node.Fqdn = node.Ipv4
		glog.Warningf("no Fqdn for %s: using IP as Fqdn", node.Ipv4)
	}
	row := []string{node.Fqdn}
	if r.EndpointDisplay.Fleet {
		row = append(row, fmt.Sprintf("https://%s:%d", node.Ipv4, config.Fleet_etcd_client_port))
	}
	if r.EndpointDisplay.Kubernetes {
		row = append(row, []string{
			fmt.Sprintf("https://%s:%d", node.Ipv4, KubernetesApiServerSecurePort),
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Kubernetes_etcd_client_port),
		}...)
	}
	if r.EndpointDisplay.Vault {
		row = append(row, []string{
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_port),
			fmt.Sprintf("https://%s:%d", node.Ipv4, config.Vault_etcd_client_port),
		}...)
	}
	return row
}

func (r *Runtime) displayEndpoints(kubernetesControlPlanes []Machine, config EnjoliverConfig) {
	if r.Output == AsciiDisplay {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		if r.HideAsciiHeader == false {
			asciiTable.SetHeader(r.createHeaderForEndpoint())
		}
		for _, node := range kubernetesControlPlanes {
			asciiTable.Append(r.createRowForEndpoint(node, config))
		}
		setAsciiTableStyleAndRender(asciiTable)
		return
	}
	if r.Output == JsonDisplay {
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
	glog.Errorf("unknown output format")
}

type Machines []Machine

func (slice Machines) Len() int {
	return len(slice)
}

func (slice Machines) Less(i, j int) bool {
	return slice[i].Fqdn < slice[j].Fqdn
}

func (slice Machines) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

func (r *Runtime) getMachineByRole(rolePath string) (Machines, error) {
	var machines Machines

	b, err := r.SmartClient(rolePath)
	if err != nil {
		return nil, err
	}
	err = json.Unmarshal(b, &machines)
	if err != nil {
		glog.Errorf("fail to unmarshal: %s", err)
		return nil, err
	}
	return machines, nil
}

func (r *Runtime) DisplayEndpoints() error {
	schedulerKubeControlPlane, err := r.getMachineByRole(SchedulerKubernetesControlPlanePath)
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	sort.Sort(schedulerKubeControlPlane)
	r.displayEndpoints(schedulerKubeControlPlane, enjoliverConfig)
	return nil
}
