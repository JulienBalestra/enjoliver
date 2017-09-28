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
	AgentHealthzPath = "/healthz"
)

var eltInRowForComponentStatus = []string{"Fqdn", "fleet-etcd", "kubelet", "rkt-api", "kube-etcd", "kube-apiserver", "vault", "vault-etcd"}

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

func (r *Runtime) queryEnjoliverAgentForHealthz(m Machine, ch chan EnjoliverAgentHealthz) {
	if m.Fqdn == "" {
		m.Fqdn = m.Ipv4
		glog.Warningf("no Fqdn for %s: using IP as Fqdn", m.Ipv4)
	}

	var healthz EnjoliverAgentHealthz
	healthz.Fqdn = m.Fqdn
	healthz.ControlPlane = m.ControlPlane

	uri := fmt.Sprintf("http://%s:%d%s", m.Ipv4, EnjoliverAgentPort, AgentHealthzPath)
	b, err := httpGetUnmarshal(uri)
	if err != nil {
		glog.Errorf("fail to fetch %s: %s", uri, err)
		healthz.Unreachable = true
		ch <- healthz
		return
	}

	err = json.Unmarshal(b, &healthz)
	if err != nil {
		glog.Errorf("fail to unmarshal response from %s: %s: %q", uri, string(b), err)
		healthz.Unreachable = true
	}
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
		go r.queryEnjoliverAgentForHealthz(m, ch)
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
			node.LivenessStatus.KubernetesApiserverInsecure,
			node.LivenessStatus.Vault,
			node.LivenessStatus.VaultEtcdClient} {
			if node.Unreachable == true {
				row = append(row, color.YellowString("unreachable"))
			} else {
				row = append(row, getColor(elt))
			}
		}
		return row
	}
	row = append(row, []string{"N/A", "N/A", "N/A", "N/A"}...)
	return row
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

func (r *Runtime) displayComponentStatus(componentStatuses EnjoliverAgentHealthzList) {
	if r.Output == AsciiDisplay {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		if r.HideAsciiHeader == false {
			asciiTable.SetHeader(eltInRowForComponentStatus)
		}
		for _, node := range componentStatuses {
			asciiTable.Append(r.createRowForComponentStatus(node))
		}
		setAsciiTableStyleAndRender(asciiTable)
		return
	}
	if r.Output == JsonDisplay {
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

	sort.Sort(componentStatuses)
	r.displayComponentStatus(componentStatuses)
	return nil
}
