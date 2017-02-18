#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
#apt-get install -y -qq python python-pip python-dev build-essential
apt-get install -y -qq python

ENJOLIVER=/opt/enjoliver

ln -sv ${ENJOLIVER}/matchbox /var/lib/matchbox

${ENJOLIVER}/manage.py validate
${ENJOLIVER}/manage.py show-config

echo "build done"