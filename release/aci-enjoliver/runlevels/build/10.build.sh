#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y python python-pip

ENJOLIVER=/opt/enjoliver

pip install -r ${ENJOLIVER}/requirements.txt || bash