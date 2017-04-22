#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

mkdir -pv ${GOPATH}/src/k8s.io/helm
cd ${GOPATH}/src/k8s.io/helm

git clone https://github.com/kubernetes/helm.git . && git checkout v${ACI_VERSION}

make bootstrap build

mv -v /go/src/k8s.io/helm/bin/tiller ${ROOTFS}/usr/bin/tiller

