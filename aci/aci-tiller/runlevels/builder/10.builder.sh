#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

mkdir -pv ${GOPATH}


apt-get update -qq
#apt-get install -y --force-yes mercurial

mkdir -pv ${GOPATH}/src/k8s.io/helm
cd ${GOPATH}/src/k8s.io/helm

curl -L https://github.com/kubernetes/helm/archive/v2.2.2.tar.gz -o helm.tar.gz

tar -xzf helm.tar.gz --strip-components=1

make bootstrap build

mv -v /go/src/k8s.io/helm/bin/tiller ${ROOTFS}/usr/bin/tiller

