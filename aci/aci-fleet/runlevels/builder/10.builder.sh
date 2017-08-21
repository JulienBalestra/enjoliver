#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail


curl -fL https://github.com/coreos/fleet/releases/download/v${ACI_VERSION}/fleet-v${ACI_VERSION}-linux-amd64.tar.gz -o fleet.tar.gz
tar -xzvf fleet.tar.gz --strip-components=1

upx fleetctl
upx -t fleetctl
upx fleetd
upx -t fleetd
mv -v fleetctl ${ROOTFS}/usr/bin/
mv -v fleetd ${ROOTFS}/usr/bin/
