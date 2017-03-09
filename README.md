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
* The Ignition is applied after a fast systemd-kexec

Each node can reboot with iPXE to be re-installed and re-join the cluster.


## Setups


### Production - Baremetal

You can take as example the `aci/aci-enjoliver` to see how the rkt container is built with `dgr`
 
 
### Development - Local KVM

Requirements:

* Linux with filesystem overlay for `dgr`
* See `apt.sh` for packages or `sudo make apt`
* See `.travis.yml` for example as setup & tests



    sudo MY_USER=julien make dev_setup
    
    
Start an interactive Kubernetes deployment of 2 nodes:


    sudo make -C app/tests check_euid_it_plans_enjolivage_disk_2_nodes
    

Connect inside:


    ./app/s.sh
    
    