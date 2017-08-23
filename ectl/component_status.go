package main

import (
	"encoding/json"
	"fmt"
	"github.com/fatih/color"
	"github.com/golang/glog"
	"github.com/olekukonko/tablewriter"
	"os"
	"sort"
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
	Fqdn           string
	Unreachable    bool
	ControlPlane   bool
}

type ComponentStatusDisplay struct {
	KubernetesControlPlane bool
	KubernetesNode         bool
}

func (r *Runtime) queryEnjoliverAgent(m Machine, ch chan EnjoliverAgentHealthz) {
	if m.Fqdn == "" {
		m.Fqdn = m.Ipv4
		glog.Errorf("no Fqdn for %s: using IP as Fqdn", m.Ipv4)
	}

	uri := fmt.Sprintf("http://%s:%d%s", m.Ipv4, enjoliverAgentPort, machineHealthzPath)
	b, err := httpGetUnmarshal(uri)
	if err != nil {
		glog.Errorf("fail to fetch %s: %s", uri, err)
		ch <- EnjoliverAgentHealthz{Fqdn: m.Fqdn, LivenessStatus: ComponentHealthz{}, Unreachable: true}
		return
	}

	var healthz EnjoliverAgentHealthz
	err = json.Unmarshal(b, &healthz)
	if err != nil {
		glog.Errorf("fail to unmarshal response from %s: %s: %q", uri, string(b), err)
		ch <- EnjoliverAgentHealthz{Fqdn: m.Fqdn, LivenessStatus: ComponentHealthz{}, Unreachable: true}
		return
	}

	healthz.Fqdn = m.Fqdn
	healthz.ControlPlane = m.ControlPlane
	ch <- healthz
	return
}

func (r *Runtime) getComponentStatus() (EnjoliverAgentHealthzList, error) {
	var enjoliverAgentHealthzList EnjoliverAgentHealthzList

	var machineList []Machine
	if r.ComponentStatusDisplay.KubernetesControlPlane == true {
		cp, err := r.getMachineByRole(SchedulerKubernetesControlPlanePath)
		if err != nil {
			glog.Errorf("fail to get Kubernetes Control planes: %s", err)
			return nil, err
		}
		for _, m := range cp {
			m.ControlPlane = true
			machineList = append(machineList, m)
		}
	}

	if r.ComponentStatusDisplay.KubernetesNode == true {
		no, err := r.getMachineByRole(SchedulerKubernetesNodePath)
		if err != nil {
			glog.Errorf("fail to get Kubernetes Nodes: %s", err)
			return nil, err
		}
		machineList = append(machineList, no...)
	}

	ch := make(chan EnjoliverAgentHealthz)
	defer close(ch)
	for _, m := range machineList {
		go r.queryEnjoliverAgent(m, ch)
	}
	for range machineList {
		enjoliverAgentHealthzList = append(enjoliverAgentHealthzList, <-ch)
	}
	return enjoliverAgentHealthzList, nil
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
		node.LivenessStatus.RktApi} {
		if node.Unreachable == true {
			row = append(row, color.YellowString("unreachable"))
		} else {
			row = append(row, getColor(elt))
		}
	}
	if node.ControlPlane == true {
		for _, elt := range []bool{
			node.LivenessStatus.KubernetesEtcdClient,
			node.LivenessStatus.Vault,
			node.LivenessStatus.VaultEtcdClient} {
			if node.Unreachable == true {
				row = append(row, color.YellowString("unreachable"))
			} else {
				row = append(row, getColor(elt))
			}
		}
	} else {
		row = append(row, []string{"N/A", "N/A", "N/A"}...)
	}
	return row
}

func (r *Runtime) createHeaderForComponentStatus() []string {
	header := []string{"Fqdn", "fleet-etcd", "kubelet", "kube-apiserver", "rkt-api", "kube-etcd", "vault", "vault-etcd"}
	return header
}

type EnjoliverAgentHealthzList []EnjoliverAgentHealthz

func (slice EnjoliverAgentHealthzList) Len() int {
	return len(slice)
}

func (slice EnjoliverAgentHealthzList) Less(i, j int) bool {
	return slice[i].Fqdn < slice[j].Fqdn
}

func (slice EnjoliverAgentHealthzList) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

func (r *Runtime) displayComponentStatus(componentStatuses EnjoliverAgentHealthzList, config EnjoliverConfig) {
	if r.Output == "ascii" {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		if r.HideAsciiHeader == false {
			asciiTable.SetHeader(r.createHeaderForComponentStatus())
		}
		asciiTable.SetRowSeparator(" ")
		asciiTable.SetColumnSeparator(" ")
		asciiTable.SetCenterSeparator("")
		for _, node := range componentStatuses {
			asciiTable.Append(r.createRowForComponentStatus(node))
		}
		asciiTable.Render()
		return
	}
	if r.Output == "json" {
		// TODO
		return
	}
	glog.Errorf("unknown output format")
}

func (r *Runtime) DisplayComponentStatus() error {
	componentStatuses, err := r.getComponentStatus()
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	sort.Sort(componentStatuses)
	r.displayComponentStatus(componentStatuses, enjoliverConfig)
	return nil
}
