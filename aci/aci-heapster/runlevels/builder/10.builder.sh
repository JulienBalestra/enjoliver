#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e
set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

mkdir -pv ${GOPATH}/src/k8s.io/heapster
cd ${GOPATH}/src/k8s.io/heapster

curl -L https://github.com/kubernetes/heapster/archive/v${ACI_VERSION}.tar.gz | tar -xzf - --strip-components=1
go get k8s.io/heapster/metrics

make

upx /go/src/k8s.io/heapster/heapster
upx -t /go/src/k8s.io/heapster/heapster
mv -v /go/src/k8s.io/heapster/heapster ${ROOTFS}/usr/bin/
#mv -v /go/src/k8s.io/heapster/eventer ${ROOTFS}/usr/bin/
