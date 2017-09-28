#!/bin/bash



. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://github.com/containous/traefik/releases/download/v${ACI_VERSION}/traefik_linux-amd64 -o traefik
chmod +x traefik

upx -q traefik
upx -t traefik
mv -v traefik ${ROOTFS}/usr/bin/