#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e
set -o pipefail

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -q curl python3-dev python-virtualenv build-essential git file openssh-client tar npm libpq-dev
VERSION=v6.11.4
curl https://nodejs.org/dist/${VERSION}/node-${VERSION}-linux-x64.tar.gz \
   | tar --strip 1 -C /usr/local -xzvf -


ln -vsf /usr/lib/python2.7/dist-packages/virtualenv.py /usr/local/bin/virtualenv
chmod +x /usr/local/bin/virtualenv

go version

python3.5 --version