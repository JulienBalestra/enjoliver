#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/coreos/rkt/releases/download/v${ACI_VERSION}/rkt_${ACI_VERSION}-1_amd64.deb -o rkt.deb
dpkg -x rkt.deb ${ROOTFS}
