# Enjoliver 

Travis-ci (com / org)

* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver-private.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver-private) - Private --push mirror and private daily builds  
* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver-release.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver-release) - Release daily builds 
* [![Build Status](https://travis-ci.com/JulienBalestra/enjoliver.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver) - Public daily builds  
* [![Build Status](https://travis-ci.org/JulienBalestra/enjoliver.svg?branch=master)](https://travis-ci.org/JulienBalestra/enjoliver) - Public


## Description

Deploy an usable Kubernetes cluster with iPXE.
    * Baremetal
    * Linux KVM

The Kubernetes Kubelet runtime is rkt.


## Setups


### Production - Baremetal

You can take as example the `aci/aci-enjoliver` to see how the rkt container is build with `dgr`
 
 
### Development - Local KVM

Requirements:

* Linux with filesystem overlay
* See `apt.sh` for packages or `sudo make apt`
* See `.travis.yml` for example as setup & tests


    sudo MY_USER=julien make dev_setup
    
    
Start an interactive Kubernetes deployment of 2 nodes:

    sudo make -C app/tests check_euid_it_plans_enjolivage_disk_2_nodes