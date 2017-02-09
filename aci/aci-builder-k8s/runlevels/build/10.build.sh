#!/bin/bash

set -ex
set -o pipefail
. /dgr/bin/functions.sh

isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive
export GODEBUG=netdns=cgo

apt-get update -q
apt-get install -y -q git curl tar build-essential rsync

curl -L https://storage.googleapis.com/golang/go1.7.5.linux-amd64.tar.gz -o /tmp/go.tar.gz
tar -C /usr/local -xzf /tmp/go.tar.gz