#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -q curl python3 python3-dev build-essential python-virtualenv git file openssh-client tar npm libpq-dev libssl-dev openssl
ln -vs /usr/lib/python2.7/dist-packages/virtualenv.py /usr/local/bin/virtualenv
chmod +x /usr/local/bin/virtualenv

mkdir -pv /opt/python
VERSION=3.5.3
curl -Lf https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz -o /opt/python/python.tar.gz
cd /opt/python
tar -xzf /opt/python/python.tar.gz --strip-components=1
./configure
make
make install

go version
