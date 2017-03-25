# Enjoliver 

Travis-ci (com / org)

* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver-private.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver-private) - Private --push mirror and private daily builds  
* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver-release.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver-release) - Release daily builds 
* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver) - Public daily builds  
* [![Build Status](https://travis-ci.org/JulienBalestra/enjoliver.svg?branch=master)](https://travis-ci.org/JulienBalestra/enjoliver) - Public


## Description

Deploy and maintain an usable Kubernetes cluster with iPXE.

* Baremetal
* Linux QEMU-KVM

The Kubernetes Kubelet runtime is rkt.

Kubernetes Apiserver, controller, scheduler and Apiserver proxies are deployed as `Pod` by a *Kubelet runonce*  

Kubernetes and Fleet have dedicated Etcd clusters.

Each Etcd cluster supports members replacement.

The configuration of each host is managed by Ignition.

During the lifecycle of the Kubernetes cluster, rolling updates are **fast** and fully controlled.
* The rolling update of the configuration changes are granted by Enjoliver API.
* The semaphore is managed by locksmith.
* The Ignition is applied after a fast systemd-kexec or normal reboot

Each node can reboot with iPXE to be re-installed and re-join the cluster.


## Current Stack

### Upstream

* etcd
* cni
* rkt
* Kubernetes
    * #PR: ~/aci/aci-hyperkube/patches
* Consul
* Vault
* CoreOS - stable channel
* dgr

### Stick

* fleet 1.0.0


## Setups


### Production - Baremetal

You can take as example the `aci/aci-enjoliver` to see how the rkt container is built with `dgr`
 
 
### Development - Local KVM

This part will soon have a better documentation.

If you still want to try you can follow this steps:

Requirements:

* **Linux** with filesystem overlay for `dgr`
* See `apt.sh` for the needed packages or `sudo make apt`
* See `.travis.yml` as a setup example & unit / integration tests

All in one dev setup:


    sudo MY_USER=julien make dev_setup
    
    
Start an interactive Kubernetes deployment of 2 nodes:

    # Generate ssh keys
    make -C app/tests testing.id_rsa
    
    # Start the deployment
    sudo make -C app/tests check_euid_it_plans_enjolivage_disk_2_nodes


The enjoliver API is available on `127.0.0.1:5000`, the user interface is behind the `/ui`

    
At the end of the setup, a kubectl proxy is running on `127.0.0.1:8001`
 
 

    ./hyperkube/hyperkube kubectl -s 127.0.0.1:8001 get cs
    NAME                 STATUS    MESSAGE              ERROR
    scheduler            Healthy   ok                   
    controller-manager   Healthy   ok                   
    etcd-0               Healthy   {"health": "true"}
    
    ./hyperkube/hyperkube kubectl -s 127.0.0.1:8001 get po --all-namespaces
    NAMESPACE     NAME                                  READY     STATUS    RESTARTS   AGE
    default       httpd-daemonset-265lc                 1/1       Running   0          2m
    default       httpd-daemonset-3229856519-n3dqt      1/1       Running   0          2m
    default       httpd-daemonset-55swx                 1/1       Running   0          2m
    kube-system   kube-apiserver-172.20.0.30            1/1       Running   0          2m
    kube-system   kube-apiserver-172.20.0.90            1/1       Running   0          3m
    kube-system   kube-controller-manager-172.20.0.90   1/1       Running   0          3m
    kube-system   kube-scheduler-172.20.0.90            1/1       Running   0          3m   


Use the experimental command-line:

    ./env/bin/python3.5 ./app/operations/commands.py ls
    Enjoliver:
      Healthy
    Lifecycle:
      AutoUpdate:   0/2
      UpToDate:     2/2
      AvgUpdate:    -
      MedUpdate:    -
      ETA:          -
    Locksmith:
      Available:  1/1
      Holders:    []
    
    Etcd Members:
      Kubernetes:
        etcdctl --endpoint http://172.20.0.90:2379
      Fleet:
        etcdctl --endpoint http://172.20.0.90:4001
    Kubernetes:
      kubectl -s 172.20.0.90:8080
    Fleet:
      fleetctl --endpoint=http://172.20.0.90:4001 --driver=etcd
      
    
    

Connect inside with `ssh`:


    ./app/s.sh
    

If everything works on your local environment you deserve a medal =)