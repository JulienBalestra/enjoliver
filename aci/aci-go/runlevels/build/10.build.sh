#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

TARGET=/tmp/go.tar.gz
curl -L https://storage.googleapis.com/golang/go1.7.5.linux-amd64.tar.gz -o ${TARGET}
tar -C /usr/local -xzf ${TARGET}

export GOROOT=/usr/local/go
export GOPATH=/go

mkdir -pv ${GOPATH}


for b in $(ls ${GOROOT}/bin/ )
do
    ln -sv ${GOROOT}/bin/${b} /usr/local/bin/${b}
done