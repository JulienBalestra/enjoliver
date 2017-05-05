#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

curl -Lf http://nodejs.org/dist/latest-v7.x/node-v${ACI_VERSION}-linux-x64.tar.gz | tar -xzf - --strip-components=1 -C ${ROOTFS}/usr
