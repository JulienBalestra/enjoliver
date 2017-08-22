#### Build inside rkt-fly

    # Ensure rkt, acserver and dgr at least are here:
    make -C ${GOPATH}/src/github.com/JulienBalestra/runtime
    
    # Build the binaries to drop inside the container linux distribution
    sudo make -C ${GOPATH}/src/github.com/JulienBalestra aci
    
    # Make the acserver listen
    sudo ${GOPATH}/src/github.com/JulienBalestra/enjoliver/runtime.acserver &
    
    # Build the container linux builder
    sudo make -C ${GOPATH}/src/github.com/JulienBalestra/enjoliver/aci/aci-container-linux install
    
    # Run it inside rkt-fly
    sudo ${GOPATH}/src/github.com/JulienBalestra/enjoliver/runtime/runtime.rkt run --volume \
      enjoliver,kind=host,source=${GOPATH}/src/github.com/JulienBalestra/enjoliver,readOnly=false \
      --stage1-path=${GOPATH}/src/github.com/JulienBalestra/enjoliver/runtime/rkt/stage1-fly.aci \
      --insecure-options=all --interactive enjoliver.local/container-linux:latest
    
    # Stop the acserver
    sudo pkill acserver # Or: fg ; ^C    
     