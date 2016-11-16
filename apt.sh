#!/usr/bin/env bash

INSTALL=""
tty -s
if [ $? -ne ]
then
    DEBIAN_FRONTEND=noninteractive
    INSTALL="-y"
fi

apt-get update -q

for p in curl python python-virtualenv qemu-kvm libvirt-bin bridge-utils golang
do
    apt-get install ${INSTALL} $p
done