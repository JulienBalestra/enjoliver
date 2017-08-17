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
apt-get install -y -qq git tar build-essential rsync xz-utils

curl https://github.com/upx/upx/releases/download/v3.94/upx-3.94-amd64_linux.tar.xz -L -o upx.tar.xz
bash
tar -xvf upx.tar.xz --strip 1
mv -v upx ${ROOTFS}/usr/bin

export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=${PATH}:/go/bin:/usr/local/go/bin


# Fetch dependencies
go get -u github.com/tools/godep
go get -u github.com/jteeuwen/go-bindata/go-bindata