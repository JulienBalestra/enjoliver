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

    git clone ${REPOSITORY} CaaS
    cd CaaS
    make
    ...
    
    make check
    ...
    Ran 79 tests in 42.501s
    
    OK (skipped=4)
    
    
    sudo make check_euid
    ...
    Ran 4 tests in 147.393s
    
    OK

    

    
# Backlog    

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