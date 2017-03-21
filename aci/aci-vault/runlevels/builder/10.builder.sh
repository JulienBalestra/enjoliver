#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail


apt-get update -qq
apt-get install -qqy unzip


curl -fL https://releases.hashicorp.com/vault/${ACI_VERSION}/vault_${ACI_VERSION}_linux_amd64.zip -o vault.zip
unzip vault.zip

mv -v vault ${ROOTFS}/usr/bin/