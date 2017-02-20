#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get autoremove
apt-get autoclean

ENJOLIVER=/opt/enjoliver

rm -Rf ${ENJOLIVER}/chain
rm -Rf ${ENJOLIVER}/cni
rm -Rf ${ENJOLIVER}/discoveryC
rm -Rf ${ENJOLIVER}/.git

find  ${ENJOLIVER}/runtime -not -name matchbox -delete || true

echo "skinny done"