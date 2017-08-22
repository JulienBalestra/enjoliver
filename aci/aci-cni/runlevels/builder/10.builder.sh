#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/containernetworking/cni/releases/download/v${ACI_VERSION}/cni-amd64-v${ACI_VERSION}.tgz -o cni.tar.gz
tar -xzvf cni.tar.gz

for b in bridge  cnitool  dhcp  flannel  host-local  ipvlan  loopback  macvlan  noop  ptp  tuning
do
    upx -q $b
    upx -t $b
    mv -v $b ${ROOTFS}/usr/bin/
done
