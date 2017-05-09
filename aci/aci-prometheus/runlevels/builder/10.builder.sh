#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -Lf https://github.com/prometheus/prometheus/releases/download/v${ACI_VERSION}/prometheus-${ACI_VERSION}.linux-amd64.tar.gz | tar -xzf - --strip-components=1

mv -v prometheus ${ROOTFS}/usr/bin/