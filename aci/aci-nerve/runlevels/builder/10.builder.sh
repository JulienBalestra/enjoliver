#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/blablacar/go-nerve/releases/download/v${ACI_VERSION}/nerve-v${ACI_VERSION}-linux-amd64.tar.gz -o nerve.tar.gz
tar -xzvf nerve.tar.gz --strip-components=1

mv -v nerve ${ROOTFS}/usr/bin/
