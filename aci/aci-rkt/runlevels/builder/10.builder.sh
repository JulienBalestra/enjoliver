#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

apt-get update -qq
apt-get install -y dh-autoreconf cpio squashfs-tools wget libacl1-dev libsystemd-dev

mkdir -pv /go/src/github.com/rkt

git clone https://github.com/rkt/rkt.git /go/src/github/rkt/rkt
cd /go/src/github/rkt/rkt

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

./autogen.sh
./configure --enable-tpm=no --with-stage1-flavors=coreos,fly
make

mkdir -pv ${ROOTFS}/usr/lib/rkt/stage1-images/

mv -v build-rkt-*/target/bin/rkt ${ROOTFS}/usr/bin/rkt
mv -v build-rkt-*/target/bin/*.aci ${ROOTFS}/usr/lib/rkt/stage1-images/
