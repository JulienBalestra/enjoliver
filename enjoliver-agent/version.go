package main

import (
	"fmt"
	"github.com/golang/glog"
	"os/exec"
	"strings"
)

type ExecForVersion struct {
	cmd         string
	arg         []string
	lines, word int
	xy          []int
}

var (
	rktVersion       = ExecForVersion{"rkt", []string{"version"}, 6, 3, []int{0, -1}}
	etcdVersion      = ExecForVersion{"etcd", []string{"--version"}, 5, 3, []int{0, -1}}
	hyperkubeVersion = ExecForVersion{"hyperkube", []string{"--version"}, 2, 2, []int{0, -1}}
	iproute2Version  = ExecForVersion{"ip", []string{"-V"}, 2, 3, []int{0, -1}}
	vaultVersion     = ExecForVersion{"vault", []string{"--version"}, 2, 3, []int{0, 1}}
	systemdVersion   = ExecForVersion{"systemctl", []string{"--version"}, 3, 2, []int{0, 1}}
	kernelVersion    = ExecForVersion{"uname", []string{"-r"}, 2, 1, []int{0, 0}}
	fleetVersion     = ExecForVersion{"fleet", []string{"--version"}, 2, 3, []int{0, -1}}
	binariesToExec   = []ExecForVersion{
		rktVersion, etcdVersion, hyperkubeVersion, iproute2Version,
		vaultVersion, systemdVersion, kernelVersion, fleetVersion,
	}
)

func getOutputOfCommand(cmd string, arg ...string) (string, error) {
	out, err := exec.Command(cmd, arg...).Output()
	if err != nil {
		glog.Errorf("fail to get output of command %s: %s", cmd, err)
		return "", err
	}
	return string(out), nil
}

func parsingError(array []string) error {
	errMsg := fmt.Sprintf("incoherent number of elt in output: %d : [%s]", len(array), strings.Join(array, ", "))
	glog.Errorf(errMsg)
	return fmt.Errorf(errMsg)
}

func getStringInTable(text string, execVersion ExecForVersion) (string, error) {
	lines := strings.Split(text, "\n")
	if len(lines) != execVersion.lines {
		return "", parsingError(lines)
	}
	words := strings.Split(lines[execVersion.xy[0]], " ")
	if len(words) != execVersion.word {
		return "", parsingError(words)
	}
	if execVersion.xy[1] == -1 {
		execVersion.xy[1] = len(words) - 1
	}
	return words[execVersion.xy[1]], nil
}

type AllComponentVersion struct {
	BinaryVersion map[string]string
	Errors        map[string]string
}

func GetComponentVersions() AllComponentVersion {
	var allComponentVersion AllComponentVersion
	allComponentVersion.BinaryVersion = make(map[string]string)
	allComponentVersion.Errors = make(map[string]string)

	for _, b := range binariesToExec {
		output, err := getOutputOfCommand(b.cmd, b.arg...)
		if err != nil {
			allComponentVersion.Errors[b.cmd] = err.Error()
			glog.Errorf("fail to get version by exec: %s", err)
			continue
		}
		allComponentVersion.BinaryVersion[b.cmd], err = getStringInTable(output, b)
		if err != nil {
			allComponentVersion.Errors[b.cmd] = err.Error()
			glog.Errorf("fail to get version by exec: %s", err)
			continue
		}

	}
	return allComponentVersion
}
