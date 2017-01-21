# Enjoliver 

[![Build Status](https://travis-ci.com/JulienBalestra/enjoliver-private.svg?token=ZwLEpiSqDoYCiBWcDCqE&branch=master)](https://travis-ci.com/JulienBalestra/enjoliver-private) *travis-ci.com* 

[![Build Status](https://travis-ci.org/JulienBalestra/enjoliver.svg?branch=master)](https://travis-ci.org/JulienBalestra/enjoliver) *travis-ci.org*


## Description

Deploy an usable Kubernetes cluster with iPXE.

The Kubernetes Kubelet runtime is rkt.

Docker:// prefix is removed from Kubernetes by patches and recompile.
Extra features are (alpha) adds like:

* easily identify who's who `systemctl list-units "k8s_*"`
* get logs of a pod by the `journalctl --identifier`
* creates volumes by pods annotations `rkt.kubernetes.io/host-create-directories: /tmp/my-dir`
* import environment variables of node / host information (IP + Hostname) inside the pod of avoid discovery process

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
    
    