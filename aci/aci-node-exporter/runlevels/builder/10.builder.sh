#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -Lf https://github.com/prometheus/node_exporter/releases/download/v${ACI_VERSION}/node_exporter-${ACI_VERSION}.linux-amd64.tar.gz | tar -xzf - --strip-components=1

upx -q node_exporter
upx -t node_exporter

mv -v node_exporter ${ROOTFS}/usr/bin/