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
	binaries         = []ExecForVersion{rktVersion, etcdVersion, hyperkubeVersion}
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

func GetBinariesVersions() map[string]string {
	binaryByVersion := make(map[string]string)

	for _, b := range binaries {
		output, err := getOutputOfCommand(b.cmd, b.arg...)
		if err != nil {
			glog.Errorf("fail to get version by exec: %s", err)
			continue
		}
		binaryByVersion[b.cmd], err = getStringInTable(output, b)
		if err != nil {
			glog.Errorf("fail to get version by exec: %s", err)
			continue
		}

	}
	return binaryByVersion
}
