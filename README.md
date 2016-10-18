# CoreOS as a Service

## Linux checkout

Requirements:

* coreutils
* make
* curl
* gpg
* python2.7
    * until now no python requirements
    


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
    

