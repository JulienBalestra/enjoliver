#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e
set -o pipefail

# export LC_ALL=C
# export GOPATH=/go
# export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}
# apt-get install python-pip virtualenv

# git clone https://github.com/ceph/ceph
# cd ceph
# ./install-deps.sh
# ./do_cmake.sh

apt-get -qy install ceph-common
mkdir -p ${ROOTFS}/opt/{lib,bin}  ${ROOTFS}/usr/lib64
set +e
ldd /usr/bin/rbd |awk '{print $3}' |grep -v '^$'|grep -E 'rados|rbd|boost' |xargs -I'{}' cp {} ${ROOTFS}/opt/lib
ldd /usr/bin/rbd |awk '{print $3}' |grep -v '^$'|grep -Ev 'rados|rbd|boost' |xargs -I'{}' cp {} ${ROOTFS}/usr/lib64

cp  /usr/bin/rbd ${ROOTFS}/opt/bin
cp /usr/lib/x86_64-linux-gnu/nss/libsoftokn3.so ${ROOTFS}/opt/lib
cp /usr/lib/x86_64-linux-gnu/libsqlite3.so.0 ${ROOTFS}/opt/lib
cp /usr/lib/x86_64-linux-gnu/nss/libfreeblpriv3.so ${ROOTFS}/opt/lib
cp /lib64/ld-linux-x86-64.so.2 ${ROOTFS}/usr/lib64
cd ${ROOTFS}
cp -a  usr/lib64 ${ROOTFS}
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/lib /opt/bin/rbd
