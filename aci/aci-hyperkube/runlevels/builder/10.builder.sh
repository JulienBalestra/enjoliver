#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

export LC_ALL=C

SOURCE_PROJECT=/opt/source-project

cp -v ${SOURCE_PROJECT}/hyperkube/hyperkube ${ROOTFS}
cd -P ${ROOTFS}
./hyperkube --make-symlinks
