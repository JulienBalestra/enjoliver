#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail


apt-get update -qq
apt-get install -qqy unzip

curl -fL https://releases.hashicorp.com/consul/${ACI_VERSION}/consul_${ACI_VERSION}_linux_amd64.zip -o consul.zip
unzip consul.zip

mv -v consul ${ROOTFS}/usr/bin/
mkdir -pv ${ROOTFS}/consul-data

curl -Lf https://releases.hashicorp.com/consul-template/0.18.2/consul-template_0.18.2_linux_amd64.tgz | \
    tar -xzvf - -C ${ROOTFS}/usr/bin