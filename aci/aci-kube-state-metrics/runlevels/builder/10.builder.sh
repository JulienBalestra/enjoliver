#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e
set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

mkdir -pv ${GOPATH}/src/k8s.io/kube-state-metrics
cd ${GOPATH}/src/k8s.io/kube-state-metrics

curl -L https://github.com/kubernetes/kube-state-metrics/archive/v${ACI_VERSION}.tar.gz | tar -xzf - --strip-components=1
make build

upx -q kube-state-metrics
upx -t kube-state-metrics

mv -v kube-state-metrics ${ROOTFS}/usr/bin/kube-state-metrics
