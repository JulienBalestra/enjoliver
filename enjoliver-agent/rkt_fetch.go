package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"os/exec"
	"strings"
	"time"

	"github.com/golang/glog"
)

const insecure_options = "--insecure-options=all"

func fetchOneImage(image string, ch chan error) {
	commandLine := []string{"rkt", "fetch"}
	if flag.Lookup(RktFetchInsecure).Value.String() == "true" {
		commandLine = append(commandLine, insecure_options)
	}
	commandLine = append(commandLine, image)
	cmd := exec.Command(commandLine[0], commandLine[1:]...)
	stderrReader, err := cmd.StderrPipe()
	if err != nil {
		glog.Errorf("fail to open pipe for stderr: %s", err)
	}
	time.AfterFunc(time.Minute*2, func() {
		cmd.Process.Kill()
	})
	cmd.Start()
	state, err := cmd.Process.Wait()
	if err != nil {
		glog.Errorf("fail run command %s: %s", strings.Join(commandLine, " "), err)
	}
	stderr, err := ioutil.ReadAll(stderrReader)
	if err != nil {
		glog.Errorf("fail to read from stderr %s: %s", strings.Join(commandLine, " "), err)
	}
	if len(stderr) > 0 {
		glog.Warningf("%s with stderr: %s", strings.Join(commandLine, " "), stderr)
	}
	if state.Success() == true {
		ch <- nil
		return
	}
	glog.Errorf("%s result fail", image)
	ch <- fmt.Errorf("%s result fail", image)
}

func (run *Runtime) RktFetch(images []string) []error {
	ch := make(chan error)
	defer close(ch)
	var results []error
	var err error
	for _, i := range images {
		go fetchOneImage(i, ch)
	}
	for range images {
		err = <-ch
		if err != nil {
			results = append(results, err)
		}
	}

	return results
}
