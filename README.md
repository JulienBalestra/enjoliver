# Enjoliver

## Linux checkout and local run

### Requirements

#### Debian / Ubuntu auto-way


    sudo apt-get update -qq
    sudo make apt
    
    # MY_USER is your non-root user
    sudo MY_USER= make setup
    make validate
    
    
    # Testing
    make check
    sudo make check_euid
    
    # Quick using
    sudo TEST=TestKVMK8SFast0 make -C app/tests/ check_euid_k8s_fast
    
    

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
    
    