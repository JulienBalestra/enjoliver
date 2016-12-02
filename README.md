# CoreOS as a Service

## Linux checkout

#### Requirements


* coreutils
* git
* make
* curl
* gpg
* python (2.7)
* virtualenv
* KVM-QEMU
* Go
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


# TODO

* QEMU-KVM doesn't restart itself when invoking systemctl reboot: stay power off 

* Safe reboot with multi factors
    * ignition change
    * GET uuid / mac on API to confirm
    
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

* Store the scheduling results in DB
    

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