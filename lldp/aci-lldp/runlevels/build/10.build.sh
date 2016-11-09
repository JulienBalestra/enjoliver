#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y lldpd

