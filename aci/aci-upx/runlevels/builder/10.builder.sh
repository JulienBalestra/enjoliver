#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

apt-get update -q
apt-get install -y -q curl tar xz-utils

UPX=3.94
curl https://github.com/upx/upx/releases/download/v${UPX}/upx-${UPX}-amd64_linux.tar.xz -L -o upx.tar.xz
tar -xvf upx.tar.xz --strip 1
mv -v upx ${ROOTFS}/usr/bin

