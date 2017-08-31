package main

import (
	"fmt"
	"github.com/coreos/go-systemd/dbus"
	"github.com/golang/glog"
	"time"
)

var k8s_units = []string{"kubelet.service", "rkt-api.service", "kube-apiserver.service", "etcd3@kubernetes.service"}

const (
	systemdUnitStopStartMode = "replace"
)

func waitUnitIs(sd *dbus.Conn, name string, states []string) error {
	const maxTries = 30

	for i := 0; i < maxTries; i++ {
		status, err := sd.ListUnitsByNames([]string{name})
		if err != nil {
			glog.Errorf("fail to get unit status %s: %s", name, err)
			return err
		}
		for _, state := range states {
			if status[0].ActiveState == state {
				return nil
			}
		}
		glog.Warningf("%d/%d unit %s status is %q", i, maxTries, name, status[0].ActiveState)
		time.Sleep(time.Millisecond * (200 * time.Duration(i)))
	}
	return fmt.Errorf("fail to get status % on %s", states, name)
}

func startUnitRetry(sd *dbus.Conn, name string) error {
	const maxTries = 10
	ch := make(chan string)
	defer close(ch)

	var status string
	for i := 0; i < maxTries; i++ {
		_, err := sd.StartUnit(name, systemdUnitStopStartMode, ch)
		if err != nil {
			glog.Errorf("fail to call dbus to start %s: %s", name, err)
			return err
		}
		status = <-ch
		if status == "done" {
			return nil
		}
		glog.Warningf("%d/%d unit %s fail to start: %s", i, maxTries, name, status)
	}
	return fmt.Errorf("unit %s fail to start with status %s", name, status)
}

func restartSystemdKubernetesStack() error {
	sd, err := dbus.New()
	if err != nil {
		glog.Errorf("fail to connect to dbus: %s", err)
		return err
	}
	defer sd.Close()

	for _, u := range k8s_units {
		glog.V(2).Infof("stopping %s", u)
		_, err = sd.StopUnit(u, systemdUnitStopStartMode, nil)
		if err != nil {
			glog.Errorf("fail to call dbus to stop %s: %s", u, err)
			break
		}
		err = waitUnitIs(sd, u, []string{"inactive", "failed"})
		if err != nil {
			glog.Errorf("fail to have status %s on %s: break", "inactive", u)
			break
		}
	}

	var badStart []error
	for i := len(k8s_units) - 1; i != -1; i-- {
		glog.V(2).Infof("starting %s", k8s_units[i])
		err = startUnitRetry(sd, k8s_units[i])
		if err != nil {
			glog.Errorf("fail to start unit %s", k8s_units[i])
		}
		err = waitUnitIs(sd, k8s_units[i], []string{"active"})
		if err != nil {
			glog.Errorf("fail to have status %q on %s", "active", k8s_units[i])
			badStart = append(badStart, err)
		}
	}

	if len(badStart) > 0 {
		glog.Errorf("fail to restart all units: %s", badStart)
		return fmt.Errorf("fail to restart all units: %s", badStart)
	}

	glog.V(2).Infof("finished to restart all units with success")
	return nil
}

func (run *Runtime) RestartKubernetes() error {

	//TODO make an etcd lock
	err := restartSystemdKubernetesStack()
	if err != nil {
		glog.Errorf("fail to restart units", err)
		return err
	}

	return nil
}
