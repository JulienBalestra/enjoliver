# Enjoliver

## Linux checkout and local run

#### Requirements

* coreutils
* file
* git
* make
* curl
* gpg
* python (2.7)
* virtualenv
* KVM-QEMU
* Go > 1.3
* iptables-restore (optional)


    kvm-ok 
    INFO: /dev/kvm exists
    KVM acceleration can be used
    
    sudo apt-get install qemu-kvm libvirt-bin bridge-utils
    which virt-install && which virsh && echo OK
    
* ipxe chain loading build
    * liblzma-dev 
    * mkisofs 
    * isolinux    


## Quick start

    make   

**If testing:**

    make check
    sudo make check_euid


## Release

    sudo make acis
    sudo make release
    ls -lh release/*.aci
    
#### Release and quick all_in_one

    sudo make run_gunicorn
    sudo make run_bootcfg
    sudo make run_all_in_one
    
    # You may need a bridge and a dnsmasq to chain loading to the API/BOOTCFG URI

# TODO

* QEMU-KVM doesn't restart itself when invoking systemctl reboot: stay power off 

* Safe reboot with multi factors
    * ignition change
    * GET uuid / mac on API to confirm
    
* Use a real disk and add the selector (e.g: &os=installing)

* Way to easily release and run
    
####     
    
    
# Backlog / No priority   

* Keep SSH config (KeyChecking)

* make assets relink twice -> because of make re 

* Avoid reset -q after lldp exit

* Refactor the lldp.aci to no depends on old style dgr builds
    * lldp/aci-base
    * lldp/aci-debian

* Keep and history of each POST discovery
    * Real db cluster for Documents (capped)

* Scheduling with persistence if Lifecycle
    * Store results in DB: the fs is always a sync representation of the db
        * staling

    * Import the fs files as persistence: backup to implement
        * concurrency limit
    

#### rkt stage for KVM-QEMU

* rkt KVM-QEMU from ubuntu 16.04 
    
    
    apt-get update
    apt-get install \
        git \
        dh-autoreconf \
        cpio \
        squashfs-tools \
        wget \
        libssl-dev \
        libacl1-dev \
        libtspi-dev \
        libsystemd-dev \
        golang \
        bc \
        realpath \
        build-essential \    
        gcc-aarch64-linux-gnu
    
    git clone https://github.com/coreos/rkt.git
     
    cd rkt
    
    ./autogen.sh && \
        ./configure \
            --with-stage1-flavors=kvm \
            --with-stage1-kvm-hypervisors=qemu && \
        make    
    # and that doesn't works    