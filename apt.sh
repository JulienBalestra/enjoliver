#!/usr/bin/env bash

tty -s
if [ -z ${INSTALL} ] && [ $? -ne ]
then
    DEBIAN_FRONTEND=noninteractive
    INSTALL="-y"
fi

apt-get update -q

for p in curl python python-virtualenv qemu-kvm libvirt-bin bridge-utils golang jq liblzma-dev mkisofs isolinux
do
    apt-get install ${INSTALL} $p
done