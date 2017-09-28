#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail


apt-get update -qq
apt-get install -y wget build-essential libreadline-dev

cd /opt

cp ${ACI_HOME}/files/hap.sh .
/opt/hap.sh

mv -v /opt/work/target/haproxy/usr/local/sbin/haproxy ${ROOTFS}/usr/sbin/haproxy