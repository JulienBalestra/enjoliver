#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

apt-get update

# deps for kube-proxy
apt-get install -y iptables module-init-tools
