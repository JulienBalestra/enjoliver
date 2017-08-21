#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

apt-get update -qq
apt-get install -y mercurial

GLIDE_VERSION=0.12.3
curl -L https://github.com/Masterminds/glide/releases/download/v${GLIDE_VERSION}/glide-v${GLIDE_VERSION}-linux-amd64.tar.gz | \
    tar -C /usr/local/bin -xzvf - --strip-components=1

mkdir -pv ${GOPATH}/src/k8s.io/helm
cd ${GOPATH}/src/k8s.io/helm

git clone https://github.com/kubernetes/helm.git . && git checkout v${ACI_VERSION}

make bootstrap build

upx /go/src/k8s.io/helm/bin/tiller
upx -t /go/src/k8s.io/helm/bin/tiller
mv -v /go/src/k8s.io/helm/bin/tiller ${ROOTFS}/usr/bin/tiller

