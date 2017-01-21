#!/usr/bin/env bash

tty -s
if [ -z ${INSTALL} ] && [ $? -ne ]
then
    DEBIAN_FRONTEND=noninteractive
    INSTALL="-yq"
fi

apt-get update -qq

apt-get install ${INSTALL} curl python python-dev python-virtualenv qemu-kvm libvirt-bin virtinstall jq liblzma-dev mkisofs isolinux file npm make

# Go version have to be > 1.3
go version || apt-get install ${INSTALL} golang
jq -h || apt-get install ${INSTALL} jq
