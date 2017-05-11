#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e
set -o pipefail

export LC_ALL=C

npm install -g yarn

git clone https://github.com/djenriquez/vault-ui.git ${ROOTFS}/opt/vault-ui

cd ${ROOTFS}/opt/vault-ui

yarn install --pure-lockfile --silent
yarn run build-web
npm prune --silent --production