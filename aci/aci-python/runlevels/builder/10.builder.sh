#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq

apt-get install -y curl \
    build-essential zlib1g-dev libbz2-dev liblzma-dev libncurses5-dev \
    libreadline6-dev libsqlite3-dev libssl-dev libgdbm-dev liblzma-dev \
    tk8.5-dev lzma lzma-dev libgdbm-dev


mkdir -pv /opt/python

# dgr give the version
VERSION=${ACI_VERSION%-*}

curl -Lf https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz -o /opt/python/python.tar.gz
cd /opt/python
tar -xzf /opt/python/python.tar.gz --strip-components=1

./configure --prefix ${ROOTFS}/usr \
    --enable-loadable-sqlite-extensions # --enable-optimizations # 1min to > 30min

make clean
make -j
make altinstall