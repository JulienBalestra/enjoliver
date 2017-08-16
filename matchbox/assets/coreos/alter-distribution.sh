#!/usr/bin/env bash

set -ex

test $(id -u -r) -eq 0
test ${VERSION}

cd $(dirname $0)
COREOS_DIRECTORY=$(pwd -P)
cd ${COREOS_DIRECTORY}/${VERSION}

P9=${COREOS_DIRECTORY}/${VERSION}/p9

mkdir -pv {squashfs,initrd} ${P9}

bzip2 -d coreos_production_image.bin.bz2
LOOP=$(losetup --find --show --partscan coreos_production_image.bin)
mount /dev/loop0p9 ${P9}

gunzip --force coreos_production_pxe_image.cpio.gz
cd initrd
cpio -id < ../coreos_production_pxe_image.cpio
cd ../squashfs
unsquashfs -no-progress ../initrd/usr.squashfs

# CWD == ~/matchbox/assets/coreos/${VERSION}/squashfs

EXCLUDES="--exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp"

ETCD_ACI=$(ls ${ACI_PATH}/etcd/etcd-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

VAULT_ACI=$(ls ${ACI_PATH}/vault/vault-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}

IPROUTE2_ACI=$(ls ${ACI_PATH}/iproute2/iproute2-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

FLEET_ACI=$(ls ${ACI_PATH}/fleet/fleet-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

HYPERKUBE_ACI=$(ls ${ACI_PATH}/hyperkube/hyperkube-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}
tar -C ${P9}/usr/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}

RKT_ACI=$(ls ${ACI_PATH}/rkt/rkt-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}

CNI_ACI=$(ls ${ACI_PATH}/cni/cni-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
tar -C ${P9}/usr -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}

sync

mksquashfs squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments
cd ../initrd
find . | cpio -o -H newc | gzip -9 > ../coreos_production_pxe_image.cpio.gz
cd ../

umount ${P9}
losetup -d ${LOOP}
bzip2 -z coreos_production_image.bin -9

rm -rf squashfs initrd coreos_production_pxe_image.cpio ${P9}