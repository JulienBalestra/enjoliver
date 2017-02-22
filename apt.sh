#!/usr/bin/env bash 

set -e

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq

apt-get install -y curl python python-dev python-virtualenv qemu-kvm libvirt-bin virtinst jq file make

# Go version have to be > 1.3
go help || apt-get install -y golang
jq -h || apt-get install -y jq

# Fix for Travis
(nodejs --version || npm --version) || apt-get install -y nodejs