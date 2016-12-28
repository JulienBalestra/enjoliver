#!/bin/bash

set -ex
set -o pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
# The static link need the latest libs
apt-get upgrade -y

export GODEBUG=netdns=cgo

ROOT_VOL=/opt/hyperkube

cd -P $(dirname $0)

export GOPATH=/go
export PATH=$PATH:/go/bin:/usr/local/go/bin

VERSION=1.5.1
VVERSION="v${VERSION}"

mkdir -pv ${GOPATH}

# Fetch dependencies
go get -u github.com/tools/godep
go get -u github.com/jteeuwen/go-bindata/go-bindata

# Fetch sources
WORK_DIR="${GOPATH}/k8s.io/kubernetes"
mkdir -pv ${WORK_DIR}
curl -fL "https://github.com/kubernetes/kubernetes/archive/${VVERSION}.tar.gz" \
    | tar xzf - -C ${WORK_DIR} --strip 1
cd ${WORK_DIR}

# Apply custom patches
PATCHES_DIR="${ROOT_VOL}/workspace/patches"
for patch in $(ls $PATCHES_DIR); do
    patch -p1 < "$PATCHES_DIR/$patch" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
done

# Build
time make hyperkube

ls -lh _output/local/go/bin/
cp -av _output/local/go/bin/hyperkube ${ROOT_VOL}