package main

import (
	"fmt"
	"os/exec"
	"strings"
	"time"

	dbus "github.com/coreos/go-systemd/dbus"
	"github.com/golang/glog"
)

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

func (run *Runtime) restartSystemdKubernetesStack() error {
	sd, err := dbus.New()
	if err != nil {
		glog.Errorf("fail to connect to dbus: %s", err)
		return err
	}
	defer sd.Close()

	for _, u := range run.KubernetesSystemdUnits {
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
	for i := len(run.KubernetesSystemdUnits) - 1; i != -1; i-- {
		glog.V(2).Infof("starting %s", run.KubernetesSystemdUnits[i])
		err = startUnitRetry(sd, run.KubernetesSystemdUnits[i])
		if err != nil {
			glog.Errorf("fail to start unit %s", run.KubernetesSystemdUnits[i])
		}
		err = waitUnitIs(sd, run.KubernetesSystemdUnits[i], []string{"active"})
		if err != nil {
			glog.Errorf("fail to have status %q on %s", "active", run.KubernetesSystemdUnits[i])
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

// action should be unlock, lock
func (run *Runtime) locksmithAction(action string) error {
	commandLine := []string{"locksmithctl", "-endpoint", run.LocksmithEndpoint, action, run.LocksmithLock}
	glog.V(2).Infof("running %q", strings.Join(commandLine, " "))
	cmd := exec.Command(commandLine[0], commandLine[1:]...)
	b, err := cmd.CombinedOutput()
	if err != nil {
		glog.Errorf("fail to run %s: %s %s", strings.Join(commandLine, " "), err, string(b))
		return err
	}
	glog.V(3).Infof("successfully run %q: %s", strings.Join(commandLine, " "), string(b))
	return nil
}

func (run *Runtime) RestartKubernetes() error {
	const maxLockTry = 10
	var err error

	// we don't want to concurrently restart the same systemd stack
	run.RestartKubernetesLock.Lock()
	defer run.RestartKubernetesLock.Unlock()

	// if it's self locked and not released
	// we are safe because after the mutex
	run.locksmithAction("unlock")

	for i := 0; i < maxLockTry; i++ {
		err = run.locksmithAction("lock")
		if err == nil {
			break
		}
		glog.Warningf("%d/%d fail to take lock %s", i, maxLockTry, err)
		time.Sleep(time.Millisecond * (200 * time.Duration(i)))
	}

	if err != nil {
		glog.Errorf("fail to take lock %s", err)
		return err
	}

	err = run.restartSystemdKubernetesStack()
	if err != nil {
		glog.Errorf("fail to restart units", err)
		return err
	}

	err = run.locksmithAction("unlock")
	if err != nil {
		glog.Errorf("fail to release the lock: %s", err)
		return err
	}
	return nil
}
