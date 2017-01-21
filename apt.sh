#!/usr/bin/env bash

tty -s
if [ -z ${INSTALL} ] && [ $? -ne ]
then
    DEBIAN_FRONTEND=noninteractive
    INSTALL="-y"
fi

apt-get update -q

for p in curl python python-virtualenv qemu-kvm libvirt-bin virtinstall jq liblzma-dev mkisofs isolinux file npm make
do
    apt-get install ${INSTALL} $p
done

# Go version have to be > 1.3
go version || apt-get install ${INSTALL} golang
jq -h || apt-get install ${INSTALL} jq
