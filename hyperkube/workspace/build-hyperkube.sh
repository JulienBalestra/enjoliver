#!/bin/bash

set -exv
set -o pipefail

export DEBIAN_FRONTEND=noninteractive
export GODEBUG=netdns=cgo

ACI_HOME=/opt/workspace

cd ${ACI_HOME}

export GOPATH=/go
export PATH=$PATH:/go/bin:/usr/local/go/bin

VERSION=1.4.5
VVERSION="v${VERSION}"

mkdir -pv ${GOPATH}

# Fetch dependencies
go get -u github.com/tools/godep
go get -u github.com/jteeuwen/go-bindata/go-bindata

# Fetch sources
WORK_DIR="${GOPATH}/k8s.io/kubernetes"
mkdir -p ${WORK_DIR}
curl -fL "https://github.com/kubernetes/kubernetes/archive/${VVERSION}.tar.gz" \
    | tar xzf - -C ${WORK_DIR} --strip 1
cd ${WORK_DIR}

# Apply custom patches
PATCHES_DIR="$ACI_HOME/patches"
for patch in $(ls $PATCHES_DIR); do
    patch -p1 < "$PATCHES_DIR/$patch" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
done

# Build
time make hyperkube

ls -lh _output/local/go/bin/
cp -a _output/local/go/bin/hyperkube ${ACI_HOME}