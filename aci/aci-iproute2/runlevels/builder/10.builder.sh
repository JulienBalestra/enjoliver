#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

apt-get update -qq
apt-get install -y bison flex

git clone git://git.kernel.org/pub/scm/linux/kernel/git/shemminger/iproute2.git

cd iproute2
git checkout v${ACI_VERSION}


# Apply custom patches
PATCHES_DIR="${ACI_HOME}/patches"
for patch in $(ls $PATCHES_DIR)
do
    echo "${PATCHES_DIR}/${patch}"
    head -4 "${PATCHES_DIR}/${patch}"
    patch -p1 < "${PATCHES_DIR}/${patch}" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
    echo ""
done

./configure
make

upx -q ip/ip
upx -t ip/ip

mv -v ip/ip ${ROOTFS}/usr/bin/ip