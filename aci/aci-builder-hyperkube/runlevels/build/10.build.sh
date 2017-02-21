#!/bin/bash

set -ex
set -o pipefail
. /dgr/bin/functions.sh

isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive
export GODEBUG=netdns=cgo

apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq git curl tar build-essential rsync

TARGET=/tmp/go.tar.gz
curl -L https://storage.googleapis.com/golang/go1.8.linux-amd64.tar.gz -o ${TARGET}
tar -C /usr/local -xzf ${TARGET}

export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=${PATH}:/go/bin:/usr/local/go/bin

rm -v ${TARGET}

mkdir -pv ${GOPATH}

# Fetch dependencies
go get -u github.com/tools/godep
go get -u github.com/jteeuwen/go-bindata/go-bindata

for b in $(ls ${GOROOT}/bin/ )
do
    ln -sv ${GOROOT}/bin/${b} /usr/local/bin/${b}
done