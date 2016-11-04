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

## Structure overview


    caas/    
    ├── app
    │   ├── api.py
    │   ├── generate_common.py
    │   ├── generate_groups.py
    │   ├── generate_profiles.py
    │   ├── generator.py
    │   ├── __init__.py
    │   ├── scheduler.py
    │   └── tests
    │       ├── assets
    │       │   ├── __init__.py
    │       │   └── test_assets_maker.py
    │       ├── dnsmasq-metal0.conf
    │       ├── euid
    │       │   ├── basic
    │       │   │   ├── __init__.py
    │       │   │   ├── test_kvm_basic_iso.py
    │       │   │   └── test_kvm_basic_pxe.py
    │       │   ├── discovery
    │       │   │   ├── __init__.py
    │       │   │   ├── test_kvm_discovery_client.py
    │       │   │   └── test_kvm_discovery_scheduler.py
    │       │   └── __init__.py
    │       ├── __init__.py
    │       ├── inte
    │       │   ├── __init__.py
    │       │   ├── test_api_advanced.py
    │       │   ├── test_api_simple.py
    │       │   └── test_bootcfg.py
    │       ├── Makefile
    │       ├── net.d
    │       │   └── 10-metal.conf
    │       ├── test_bootcfg
    │       │   ├── assets -> ../../../bootcfg/assets/
    │       │   ├── groups
    │       │   ├── ignition
    │       │   │   ├── euid-testkvmbasiciso-test_00.yaml
    │       │   │   ├── euid-testkvmbasiciso-test_01.yaml
    │       │   │   ├── euid-testkvmbasiciso-test_02-0.yaml
    │       │   │   ├── euid-testkvmbasiciso-test_02-1.yaml
    │       │   │   ├── euid-testkvmbasiciso-test_02-2.yaml
    │       │   │   ├── euid-testkvmbasicpxe-test_00.yaml
    │       │   │   ├── euid-testkvmbasicpxe-test_01.yaml
    │       │   │   ├── euid-testkvmdiscoveryclient-test_00.yaml
    │       │   │   ├── euid-testkvmdiscoveryclient-test_01.yaml
    │       │   │   ├── euid-testkvmdiscoveryscheduler-test_00-emember.yaml
    │       │   │   ├── euid-testkvmdiscoveryscheduler-test_00.yaml
    │       │   │   ├── euid-testkvmdiscoveryscheduler-test_01-emember.yaml
    │       │   │   ├── euid-testkvmdiscoveryscheduler-test_01.yaml
    │       │   │   ├── inte-testapiadvanced-test_04_ipxe.yaml
    │       │   │   ├── inte-testapiadvanced-test_05_ipxe_selector.yaml
    │       │   │   ├── inte-testapi-test_04_ipxe.yaml
    │       │   │   ├── inte-testapi-test_05_ipxe_selector.yaml
    │       │   │   ├── inte-testbootconfighelloworld.yaml
    │       │   │   ├── inte-testbootconfigselectors-default.yaml
    │       │   │   ├── inte-testbootconfigselectors-one.yaml
    │       │   │   ├── inte-testbootconfigselectors-two.yaml
    │       │   │   ├── inte-testbootconfigselector.yaml
    │       │   │   └── unit-testetcdscheduler-test_00-emember.yaml
    │       │   ├── misc
    │       │   └── profiles
    │       └── unit
    │           ├── __init__.py
    │           ├── test_api.py
    │           ├── test_generate_groups.py
    │           ├── test_generate_profiles.py
    │           └── test_scheduler.py
    ├── bootcfg
    │   ├── assets
    │   │   ├── coreos
    │   │   │   └── Makefile
    │   │   ├── discoveryC
    │   │   │   └── Makefile
    │   │   └── setup-network-environment
    │   │       ├── 1.0.1-setup-network-environment.sha512
    │   │       └── Makefile
    │   ├── groups
    │   ├── ignition
    │   ├── misc
    │   └── profiles
    ├── chain
    │   ├── chain.ipxe.template
    │   ├── ipxe
    │   └── Makefile
    ├── discoveryC
    │   ├── config.go
    │   ├── config_test.go
    │   ├── main.go
    │   ├── Makefile
    │   ├── netnet.go
    │   ├── netnet_test.go
    │   ├── poster.go
    │   └── poster_test.go
    ├── Makefile
    ├── README.md
    └── requirements.txt
    
    27 directories, 69 files



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