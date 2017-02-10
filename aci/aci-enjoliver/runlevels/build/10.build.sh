#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq python python-pip python-dev build-essential

ENJOLIVER=/opt/enjoliver

ln -sv ${ENJOLIVER}/bootcfg /var/lib/bootcfg
pip install --upgrade pip
pip install -r ${ENJOLIVER}/requirements.txt

pip freeze

ln -sv /usr/local/bin/gunicorn /usr/bin/gunicorn

${ENJOLIVER}/validate.py

bootcfg --version

echo "build done"