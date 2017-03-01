#!/dgr/bin/busybox sh
set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive


apt-get update -qq
apt-get install -y python3.5

apt-get autoclean
apt-get autoremove
