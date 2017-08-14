#!/usr/bin/env bash

set -ex

cd ${VERSION}
mkdir -pv {squashfs,initrd}
gunzip --force coreos_production_pxe_image.cpio.gz
cd initrd
cpio -id < ../coreos_production_pxe_image.cpio 
cd ../squashfs
unsquashfs -no-progress ../initrd/usr.squashfs

ETCD_ACI=$(ls ${ACI_PATH}/etcd/etcd-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

VAULT_ACI=$(ls ${ACI_PATH}/vault/vault-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

IPROUTE2_ACI=$(ls ${ACI_PATH}/iproute2/iproute2-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

FLEET_ACI=$(ls ${ACI_PATH}/fleet/fleet-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

HYPERKUBE_ACI=$(ls ${ACI_PATH}/hyperkube/hyperkube-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

RKT_ACI=$(ls ${ACI_PATH}/rkt/rkt-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

CNI_ACI=$(ls ${ACI_PATH}/cni/cni-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${CNI_ACI} rootfs/usr --strip 2 --exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp

mksquashfs squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments
cd ../initrd
find .| cpio -o -H newc | gzip  > ../coreos_production_pxe_image.cpio.gz
cd ../
rm -rf squashfs initrd coreos_production_pxe_image.cpio