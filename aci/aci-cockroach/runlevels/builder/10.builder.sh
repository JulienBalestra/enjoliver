#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

curl -fL https://binaries.cockroachdb.com/cockroach-latest.linux-amd64.tgz -o cockroach.tar.gz
tar -xzvf cockroach.tar.gz --strip-components=1

mv -v cockroach ${ROOTFS}/usr/bin/
