package main

import (
	"net/http"
	"github.com/golang/glog"
	"os"
	"fmt"
	"sync"
	"encoding/json"
	"flag"
	"io/ioutil"
)

type Healthz struct {
	EtcdFleet           bool
	EtcdVault           bool
	EtcdKubernetes      bool
	KubernetesApiServer bool
	Kubelet             bool
	Vault               bool
}

func getHealthMessage(url string) (string, error) {
	resp, err := http.Get(url)
	if err != nil {
		glog.Errorf("fail to get %s: %s", url, err)
		return "", err
	}
	// TODO add code
	defer resp.Body.Close()

	b, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		glog.Errorf("fail to read body from url %s: %s", url, err)
		return "", err
	}
	return string(b), nil
}

type HealthMessage struct {
	URL             string
	ExpectedMessage string
}

func fillHealthStatus(status *bool, healthMessage HealthMessage, wg *sync.WaitGroup) error {

	defer wg.Done()

	//url := fmt.Sprintf("http://127.0.0.1:%d/health", port)
	msg, err := getHealthMessage(healthMessage.URL)
	if err != nil {
		glog.Errorf("fail to get health message: %s", err)
		return err
	}
	glog.V(2).Infof("message replied by etcd: %s", msg)
	if msg != healthMessage.ExpectedMessage {
		glog.Errorf("fail to compare: %s != %d", msg, healthMessage.ExpectedMessage)
		return fmt.Errorf("etcd %s %s", healthMessage.URL, msg)
	}
	*status = true
	return nil
}

type HealthReport struct {
	Health Healthz
	wg     sync.WaitGroup
}

func (ec *EnjoliverConfig) getHealthz() (Healthz, error) {
	const etcdHealthyMessage = "{\"health\": \"true\"}"
	const kubeHealthyMessage = "ok"
	const vaultHealthyMessage = "{\"errors\":[]}\n"
	var healthReport Healthz
	var wg sync.WaitGroup

	wg.Add(6)

	// etcd members
	go fillHealthStatus(&healthReport.EtcdFleet, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/health", ec.FleetEtcdClientPort),
		etcdHealthyMessage,
	}, &wg)
	go fillHealthStatus(&healthReport.EtcdKubernetes, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/health", ec.KubernetesEtcdClientPort),
		etcdHealthyMessage,
	}, &wg)
	go fillHealthStatus(&healthReport.EtcdVault, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/health", ec.VaultEtcdClientPort),
		etcdHealthyMessage,
	}, &wg)

	// Kubernetes components
	go fillHealthStatus(&healthReport.Kubelet, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/healthz", ec.KubeletPort),
		kubeHealthyMessage,
	}, &wg)
	go fillHealthStatus(&healthReport.KubernetesApiServer, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/healthz", ec.KubernetesApiServerPort),
		kubeHealthyMessage,
	}, &wg)

	// Vault
	go fillHealthStatus(&healthReport.Vault, HealthMessage{
		fmt.Sprintf("http://127.0.0.1:%d/v1/", ec.VaultPort),
		vaultHealthyMessage,
	}, &wg)

	wg.Wait()

	return healthReport, nil
}

func (ec *EnjoliverConfig) handlerHealthz(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		health, err := ec.getHealthz()
		if err != nil {
			glog.Errorf("fail to get health status: %s", err)
			return
		}

		b, err := json.Marshal(&health)
		if err != nil {
			glog.Errorf("fail to marshal health: %s", err)
			return
		}

		_, err = w.Write(b)
		if err != nil {
			glog.Errorf("fail to write %s on response: %s", string(b), err)
		}
	}
}

func main() {
	flag.Parse()
	flag.Lookup("alsologtostderr").Value.Set("true")

	glog.V(2).Infof("starting node-agent")
	ec, err := getConfig()
	if err != nil {
		glog.Errorf("fail to get config: %s", err)
		os.Exit(2)
	}

	http.HandleFunc("/healthz", ec.handlerHealthz)
	glog.Fatal(http.ListenAndServe("0.0.0.0:8000", nil))
}
