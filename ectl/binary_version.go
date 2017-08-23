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
	machineBinaryVersionPath = "/version"
)

var eltInRow = []string{"Fqdn", "Etcd", "Fleetd", "Hyperkube", "Iproute2", "Rkt", "Systemd", "Kernel", "Vault"}

type BinaryVersion struct {
	Etcd, Fleet, Hyperkube, Ip, Rkt, Systemctl, Uname, Vault string
}

type EnjoliverAgentVersion struct {
	BinaryVersion BinaryVersion
	Fqdn          string
	Unreachable   bool
}

type BinaryVersionDisplay struct {
	KubernetesControlPlane bool
	KubernetesNode         bool
}

func (r *Runtime) queryEnjoliverAgentForVersion(m Machine, ch chan EnjoliverAgentVersion) {
	if m.Fqdn == "" {
		m.Fqdn = m.Ipv4
		glog.Warningf("no Fqdn for %s: using IP as Fqdn", m.Ipv4)
	}

	var version EnjoliverAgentVersion
	version.Fqdn = m.Fqdn

	uri := fmt.Sprintf("http://%s:%d%s", m.Ipv4, enjoliverAgentPort, machineBinaryVersionPath)
	b, err := httpGetUnmarshal(uri)
	if err != nil {
		glog.Errorf("fail to fetch %s: %s", uri, err)
		version.Unreachable = true
		ch <- version
		return
	}

	err = json.Unmarshal(b, &version)
	if err != nil {
		glog.Errorf("fail to unmarshal response from %s: %s: %q", uri, string(b), err)
		version.Unreachable = true
	}
	ch <- version
	return
}

func (r *Runtime) getBinaryVersion() (EnjoliverAgentBinaryVersionList, error) {
	var EnjoliverAgentBinaryVersion EnjoliverAgentBinaryVersionList

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

	ch := make(chan EnjoliverAgentVersion)
	defer close(ch)
	for _, m := range machineList {
		go r.queryEnjoliverAgentForVersion(m, ch)
	}
	for range machineList {
		EnjoliverAgentBinaryVersion = append(EnjoliverAgentBinaryVersion, <-ch)
	}
	return EnjoliverAgentBinaryVersion, nil
}

func (r *Runtime) createRowForBinaryVersion(node EnjoliverAgentVersion) []string {
	row := []string{}
	for _, r := range []string{
		node.Fqdn,
		node.BinaryVersion.Etcd,
		node.BinaryVersion.Fleet,
		node.BinaryVersion.Hyperkube,
		node.BinaryVersion.Ip,
		node.BinaryVersion.Rkt,
		node.BinaryVersion.Systemctl,
		node.BinaryVersion.Uname,
		node.BinaryVersion.Vault,
	} {
		row = append(row, r)
	}
	return row
}

type EnjoliverAgentBinaryVersionList []EnjoliverAgentVersion

func (slice EnjoliverAgentBinaryVersionList) Len() int {
	return len(slice)
}

func (slice EnjoliverAgentBinaryVersionList) Less(i, j int) bool {
	return slice[i].Fqdn < slice[j].Fqdn
}

func (slice EnjoliverAgentBinaryVersionList) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

func (r *Runtime) displayBinaryVersion(binaryVersion EnjoliverAgentBinaryVersionList, config EnjoliverConfig) {
	if r.Output == "ascii" {
		asciiTable := tablewriter.NewWriter(os.Stdout)
		if r.HideAsciiHeader == false {
			asciiTable.SetHeader(eltInRow)
		}
		asciiTable.SetRowSeparator(" ")
		asciiTable.SetColumnSeparator(" ")
		asciiTable.SetCenterSeparator("")
		for _, node := range binaryVersion {
			asciiTable.Append(r.createRowForBinaryVersion(node))
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

func (r *Runtime) DisplayBinaryVersion() error {
	binaryVersion, err := r.getBinaryVersion()
	if err != nil {
		return err
	}

	enjoliverConfig, err := r.getEnjoliverConfig()
	if err != nil {
		return err
	}

	sort.Sort(binaryVersion)
	r.displayBinaryVersion(binaryVersion, enjoliverConfig)
	return nil
}
