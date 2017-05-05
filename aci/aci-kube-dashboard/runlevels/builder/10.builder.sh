#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e
set -o pipefail

export LC_ALL=C
export GOPATH=/go
export PATH=${GOPATH}/bin:/usr/local/go/bin:${PATH}

apt-get update -qq
apt-get install -y python openjdk-7-jre-headless

mkdir -pv ${GOPATH}/src/github.com/kubernetes/dashboard
cd ${GOPATH}/src/github.com/kubernetes/dashboard

curl -Lf https://github.com/kubernetes/dashboard/archive/v${ACI_VERSION}.tar.gz | tar -xzf - --strip-components=1

npm install -g node-gyp
npm install -g gulp
npm install -g bower

npm install

./build/postinstall.sh

gulp build

mv -v dist/amd64/dashboard ${ROOTFS}/usr/bin/
