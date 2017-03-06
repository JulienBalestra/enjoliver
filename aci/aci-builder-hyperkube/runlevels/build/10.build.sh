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
apt-get install -y -qq git tar build-essential rsync

export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=${PATH}:/go/bin:/usr/local/go/bin


# Fetch dependencies
go get -u github.com/tools/godep
go get -u github.com/jteeuwen/go-bindata/go-bindata
