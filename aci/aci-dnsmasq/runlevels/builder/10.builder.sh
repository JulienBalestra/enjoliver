#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

apt-get update -q
apt-get install -y -q curl

TFTP_DIR=${ROOTFS}/var/lib/tftpboot

mkdir -pv ${TFTP_DIR}

curl -fL -o ${TFTP_DIR}/undionly.kpxe http://boot.ipxe.org/undionly.kpxe
ln -sv ${TFTP_DIR}/undionly.kpxe ${TFTP_DIR}/undionly.kpxe.0

curl -fL -o ${TFTP_DIR}/grub.efi https://stable.release.core-os.net/amd64-usr/current/coreos_production_pxe_grub.efi

