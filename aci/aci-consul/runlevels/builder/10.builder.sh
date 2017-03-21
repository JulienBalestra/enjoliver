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