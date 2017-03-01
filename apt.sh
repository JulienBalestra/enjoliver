#!/usr/bin/env bash 

set -e

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq

apt-get install -y curl python3 python3-dev python-virtualenv qemu-kvm libvirt-bin virtinst jq file build-essential libpq-dev

# Go version have to be > 1.4
go help || apt-get install -y golang
jq -h || apt-get install -y jq

# Fix for Travis
(nodejs --version || npm --version) || apt-get install -y nodejs
npm --version || apt-get install -y npm
