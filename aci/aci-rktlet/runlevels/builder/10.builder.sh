#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

apt-get update -qq

mkdir -pv /go/src/github.com/kubernetes-incubator/rktlet

git clone https://github.com/kubernetes-incubator/rktlet /go/src/github.com/kubernetes-incubator/rktlet
cd /go/src/github.com/kubernetes-incubator/rktlet

git config --global user.email "julien.balestra@gmail.com"
git config --global user.name "JulienBalestra"

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

make

mv -v bin/rktlet ${ROOTFS}/usr/bin/rktlet