package main

import (
	"fmt"
	"os/exec"
	"strings"

	"encoding/json"
	"github.com/golang/glog"
	"io/ioutil"
)

type ExecForVersion struct {
	cmd         string
	arg         []string
	lines, word int
	xy          []int
}

// Quite technical but covered by tests
var (
	rktVersion       = ExecForVersion{"rkt", []string{"version"}, 6, 3, []int{0, -1}}
	etcdVersion      = ExecForVersion{"etcd", []string{"--version"}, 5, 3, []int{0, -1}}
	hyperkubeVersion = ExecForVersion{"hyperkube", []string{"--version"}, 2, 2, []int{0, -1}}
	iproute2Version  = ExecForVersion{"ip", []string{"-V"}, 2, 3, []int{0, -1}}
	vaultVersion     = ExecForVersion{"vault", []string{"--version"}, 2, 3, []int{0, 1}}
	systemdVersion   = ExecForVersion{"systemctl", []string{"--version"}, 3, 2, []int{0, 1}}
	kernelVersion    = ExecForVersion{"uname", []string{"-r"}, 2, 1, []int{0, 0}}
	fleetVersion     = ExecForVersion{"fleet", []string{"--version"}, 2, 3, []int{0, -1}}
	haproxyVersion   = ExecForVersion{"haproxy", []string{"-v"}, 4, 4, []int{0, 2}}
	binariesToExec   = []ExecForVersion{
		rktVersion, etcdVersion, hyperkubeVersion, iproute2Version, vaultVersion, systemdVersion, kernelVersion,
		fleetVersion, haproxyVersion,
	}
)

type BinaryResult struct {
	Cmd     string
	Version string
	Error   error
}

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

func execBinaryToParseVersion(b ExecForVersion, ch chan BinaryResult) {
	br := BinaryResult{Cmd: b.cmd}
	output, err := getOutputOfCommand(b.cmd, b.arg...)
	if err != nil {
		br.Error = err
		glog.Errorf("fail to get version by exec: %s", err)
		ch <- br
		return
	}
	br.Version, err = getStringInTable(output, b)
	if err != nil {
		br.Error = err
		glog.Errorf("fail to get version by exec: %s", err)
	}
	ch <- br
}

type ContainerLinuxVersion struct {
	Release        string `json:"release"`
	AlterTimestamp string `json:"alter_timestamp"`
	Commit         string `json:"commit"`
}

// Read the file dropped into the distribution to track release and build / alter date
func getContainerLinuxAlterVersion() BinaryResult {
	const alterVersionFile = "/usr/local/etc/alter-version"
	var br BinaryResult
	br.Cmd = "distribution"

	b, err := ioutil.ReadFile(alterVersionFile)
	if err != nil {
		glog.Errorf("fail to read file %s: %s", alterVersionFile, err)
		br.Error = err
		return br
	}

	var clv ContainerLinuxVersion
	err = json.Unmarshal(b, &clv)
	if err != nil {
		glog.Errorf("fail to unmarshal %q: %s", string(b), err)
		br.Error = err
		return br
	}
	br.Version = fmt.Sprintf("%s@%s:%s", clv.Release, clv.AlterTimestamp, clv.Commit)
	return br
}

func GetComponentVersion() AllComponentVersion {
	var allComponentVersion AllComponentVersion
	allComponentVersion.BinaryVersion = make(map[string]string)
	allComponentVersion.Errors = make(map[string]string)

	ch := make(chan BinaryResult)
	defer close(ch)
	for _, b := range binariesToExec {
		go execBinaryToParseVersion(b, ch)
	}
	for range binariesToExec {
		bv := <-ch
		allComponentVersion.BinaryVersion[bv.Cmd] = bv.Version
		if bv.Error != nil {
			allComponentVersion.Errors[bv.Cmd] = bv.Error.Error()
		}
	}
	containerLinuxVersion := getContainerLinuxAlterVersion()
	allComponentVersion.BinaryVersion[containerLinuxVersion.Cmd] = containerLinuxVersion.Version
	if containerLinuxVersion.Error != nil {
		allComponentVersion.BinaryVersion[containerLinuxVersion.Cmd] = containerLinuxVersion.Error.Error()
	}
	return allComponentVersion
}
