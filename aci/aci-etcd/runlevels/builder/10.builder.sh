#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/coreos/etcd/releases/download/v${ACI_VERSION}/etcd-v${ACI_VERSION}-linux-amd64.tar.gz -o etcd.tar.gz
tar -xzvf etcd.tar.gz --strip-components=1

mv -v etcdctl ${ROOTFS}/usr/bin/
mv -v etcd ${ROOTFS}/usr/bin/
