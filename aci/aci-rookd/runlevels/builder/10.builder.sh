#!/bin/bash
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e
set -o pipefail

export LC_ALL=C
readonly VERSION=${ACI_VERSION%-*}
readonly NAME=rook
mkdir -p ${ROOTFS}/usr/bin
readonly URL=https://github.com/${NAME}/${NAME}/releases/download/v${VERSION}/${NAME}-v${VERSION}-linux-amd64.tar.gz
echo_green "=== Fetching ${NAME}:${VERSION} ==="
echo_green "=== Fetching ${URL} ==="
curl -fL ${URL} -o ${NAME}.tar.gz
echo_green "=== Untaring ${NAME} ==="
tar -C ${ROOTFS}/usr/bin -xzvf ${NAME}.tar.gz
