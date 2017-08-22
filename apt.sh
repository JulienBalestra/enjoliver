#!/usr/bin/env bash 

set -ex

export DEBIAN_FRONTEND=noninteractive

ENJOLIVER_ENGINE="python3 python3-dev python-virtualenv libpq-dev libpq5 build-essential"
ENJOLIVER_KVM_E2E="qemu-kvm libvirt-bin virtinst jq file systemd"
CONTAINER_LINUX_ALTER="curl sudo python python2.7 bzip2 cgpt cryptsetup-bin squashfs-tools make parted cpio"

apt-get update -qq

apt-get install -y ${ENJOLIVER_ENGINE} ${ENJOLIVER_KVM_E2E} ${CONTAINER_LINUX_ALTER}

# Go version have to be > 1.4
go help || apt-get install -y golang
jq -h || apt-get install -y jq

# Fix for Travis
(nodejs --version || npm --version) || apt-get install -y nodejs
npm --version || apt-get install -y npm
