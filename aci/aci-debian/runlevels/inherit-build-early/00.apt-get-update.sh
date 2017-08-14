#!/bin/bash
set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

[ $(ls -1  /dgr/builder/runlevels/build |wc -l ) -eq 0 ] && exit 0
[ ! -z ${APT_PROXY} ] && echo "Acquire::http { Proxy 'http://${APT_PROXY}'; };" >> /etc/apt/apt.conf.d/01proxy
echo_green "==== Apt-get update ===="
apt-get -qqy update
