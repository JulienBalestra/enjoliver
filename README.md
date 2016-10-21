# CoreOS as a Service

## Linux checkout

#### Requirements


* coreutils
* git
* make
* curl
* gpg
* python2.7
    * until now no python requirements
    
* ipxe chain loading build
    * liblzma-dev 
    * mkisofs 
    * isolinux    


* rkt KVM-QEMU LKVM from ubuntu 16.04
    * git
    * dh-autoreconf
    * cpio
    * squashfs-tools 
    * wget
    * libssl-dev
    * libacl1-dev
    * libtspi-dev
    * libsystemd-dev
    * golang
    * bc

    
    git clone https://github.com/coreos/rkt.git
    ./autogen.sh && \
        ./configure \
            --with-stage1-flavors=kvm \
            --with-stage1-kvm-hypervisors=lkvm,qemu && \
        make    
    # and that doesn't works



    git clone ${REPOSITORY} CaaS
    cd CaaS
    make check
    
Should produce the following output:

    make -C app/tests/ check    
    ...   
    ...   
    ...   
    
    ----------------------------------------------------------------------
    Ran X tests in XX.XXXs
    
    OK
    make[1]: Leaving directory 'XX/CaaS/app/tests'
    

