# Enjoliver 

[![Build Status](https://travis-ci.com/JulienBalestra/enjoliver.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver)
 
[![CircleCI](https://circleci.com/gh/JulienBalestra/enjoliver/tree/master.svg?style=svg)](https://circleci.com/gh/JulienBalestra/enjoliver/tree/master)

Deploy an usable Kubernetes cluster with iPXE.

The Kubernetes Kubelet runtime is rkt.



## Linux checkout and local run

### Requirements

#### Debian / Ubuntu auto-way


    sudo apt-get update -qq
    sudo make apt
    
    # MY_USER is your non-root user
    sudo MY_USER=${USER} make setup
    make validate
        
    # Testing
    make check
    sudo make check_euid
    
    # Quick using
    sudo make -C app/tests/ check_euid_it_k8s_fast
    
    # Stop the cluster
    echo "" > /tmp/e.stop
    
    

#### Handy way

##### Mandatory:

* curl
* python
* python-virtualenv
* qemu-kvm
* libvirt-bin
* virtinstall
* jq
* file
* golang # > 1.3


    ./apt.sh # Over Debian-based


##### Optional:

* npm
* liblzma-dev
* mkisofs
* isolinux


## Release

    sudo make acis
    sudo make release
    ls -lh release/*.aci
    
    