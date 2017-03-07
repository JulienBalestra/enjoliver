#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

export LC_ALL=C
export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=$PATH:/go/bin:/usr/local/go/bin


# Fetch sources
WORK_DIR="${GOPATH}/k8s.io/kubernetes"
mkdir -p ${WORK_DIR}
curl -sLf "https://github.com/kubernetes/kubernetes/archive/v${ACI_VERSION}.tar.gz" \
    | tar xzf - -C ${WORK_DIR} --strip 1
cd ${WORK_DIR}

# Apply custom patches
PATCHES_DIR="${ACI_HOME}/patches"
for patch in $(ls $PATCHES_DIR)
do
    patch -p1 < "${PATCHES_DIR}/${patch}" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
done

# Build
make hyperkube

#cp -v _output/local/go/bin/hyperkube /opt/source-project/hyperkube
cp -v _output/local/go/bin/hyperkube ${ROOTFS}
cd -P ${ROOTFS}
./hyperkube --make-symlinks
