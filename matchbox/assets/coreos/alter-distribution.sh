#!/usr/bin/env bash

set -ex

test $(id -u -r) -eq 0
test ${VERSION}

cd $(dirname $0)
COREOS_DIRECTORY=$(pwd -P)
cd ${COREOS_DIRECTORY}/${VERSION}

USR_A=${COREOS_DIRECTORY}/${VERSION}/usr-a

mkdir -pv {squashfs,initrd} ${USR_A}

bzip2 -d coreos_production_image.bin.bz2
${COREOS_DIRECTORY}/disk.py rw

LOOP=$(losetup --find --show --partscan coreos_production_image.bin)
mount ${LOOP}p3 ${USR_A}

gunzip --force coreos_production_pxe_image.cpio.gz
cd initrd
cpio -id < ../coreos_production_pxe_image.cpio
cd ../squashfs
unsquashfs -no-progress ../initrd/usr.squashfs

# CWD == ~/matchbox/assets/coreos/${VERSION}/squashfs

EXCLUDES="--exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp"

ETCD_ACI=$(ls ${ACI_PATH}/etcd/etcd-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

VAULT_ACI=$(ls ${ACI_PATH}/vault/vault-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}

IPROUTE2_ACI=$(ls ${ACI_PATH}/iproute2/iproute2-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

FLEET_ACI=$(ls ${ACI_PATH}/fleet/fleet-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}

RKT_ACI=$(ls ${ACI_PATH}/rkt/rkt-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}

CNI_ACI=$(ls ${ACI_PATH}/cni/cni-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}

HYPERKUBE_ACI=$(ls ${ACI_PATH}/hyperkube/hyperkube-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}
tar -C ${USR_A}/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}

sync

umount ${USR_A}
losetup -d ${LOOP}

${COREOS_DIRECTORY}/disk.py ro
bzip2 -z coreos_production_image.bin -9

# Do the signing

mksquashfs squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments
cd ../initrd
find . | cpio -o -H newc | gzip -9 > ../coreos_production_pxe_image.cpio.gz
cd ../

rm -rf squashfs initrd coreos_production_pxe_image.cpio ${USR_A}