#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/containernetworking/cni/releases/download/v${ACI_VERSION}/cni-amd64-v${ACI_VERSION}.tgz | tar -xzvf -
curl -fL https://github.com/containernetworking/plugins/releases/download/v${ACI_VERSION}/cni-v${ACI_VERSION}.tgz | tar -xzvf -

for b in cnitool noop bridge dhcp flannel host-local ipvlan loopback macvlan portmap ptp sample tuning vlan
do
    upx -q $b
    upx -t $b
    mv -v $b ${ROOTFS}/usr/bin/
done
