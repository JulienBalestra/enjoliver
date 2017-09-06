#!/usr/bin/env bash

set -ex

test $(id -u -r) -eq 0
test ${VERSION}
test ${COMMIT_ID}

cd $(dirname $0)
COREOS_DIRECTORY=$(pwd -P)
ASSETS_DIRECTORY=$(dirname ${COREOS_DIRECTORY})
export VERSION_DIR=${COREOS_DIRECTORY}/${VERSION}

cd ${VERSION_DIR}
export USR_A=${VERSION_DIR}/usr-a
export BOOT=${VERSION_DIR}/boot
export VERSION

mkdir -pv {squashfs,initrd} ${USR_A} ${BOOT}

bzip2 -fdk coreos_production_image.bin.bz2
${COREOS_DIRECTORY}/disk.py rw

LOOP=$(losetup --find --show coreos_production_image.bin)
partprobe ${LOOP}

set +e
umount ${LOOP}p3 ${USR_A}
umount ${LOOP}p1 ${BOOT}
set -e

mount ${LOOP}p3 ${USR_A}
mount ${LOOP}p1 ${BOOT}
gunzip -c --force coreos_production_pxe_image.cpio.gz > coreos_production_pxe_image.cpio
cd initrd
cpio -id < ../coreos_production_pxe_image.cpio
cd ../squashfs
unsquashfs -no-progress ../initrd/usr.squashfs

_remove_in_fs(){
    for fs in squashfs-root/ ${USR_A}
    do
        rm -fv ${fs}/${1}
    done
}

_upx_in_fs() {
    for fs in squashfs-root/ ${USR_A}
    do
        upx -q ${fs}/${1}
        upx -t ${fs}/${1}
    done
}

# CWD == ~/matchbox/assets/coreos/${VERSION}/squashfs

EXCLUDES="--exclude rootfs/dgr --exclude rootfs/etc --exclude rootfs/tmp --exclude rootfs/run --exclude rootfs/sys"

for useless in /bin/docker /bin/coreos-metadata /bin/containerd /bin/containerd-shim /bin/dockerd /bin/runc \
    /bin/docker-containerd-shim /bin/docker-containerd /bin/docker-runc /bin/ctr /bin/docker-proxy /bin/mayday \
    /bin/actool /bin/tpmd
do
    _remove_in_fs ${useless}
done


_remove_in_fs /bin/etcd2
_remove_in_fs /bin/etcdctl
ETCD_ACI=$(ls ${ACI_PATH}/etcd/etcd-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${ETCD_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


VAULT_ACI=$(ls ${ACI_PATH}/vault/vault-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${VAULT_ACI} rootfs/usr/ --strip 2 ${EXCLUDES}


_remove_in_fs /bin/ip
IPROUTE2_ACI=$(ls ${ACI_PATH}/iproute2/iproute2-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${IPROUTE2_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


_remove_in_fs /bin/fleetd
_remove_in_fs /bin/fleetctl
FLEET_ACI=$(ls ${ACI_PATH}/fleet/fleet-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${FLEET_ACI} rootfs/usr/bin --strip 2 ${EXCLUDES}


_remove_in_fs /bin/rkt /lib64/rkt/stage1-images/stage1-fly.aci /lib64/rkt/stage1-images/stage1-coreos.aci
RKT_ACI=$(ls ${ACI_PATH}/rkt/rkt-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}
tar -C ${USR_A}/ -xvf ${RKT_ACI} rootfs/usr --keep-directory-symlink --strip 2 ${EXCLUDES}


mkdir -pv squashfs-root/local/cni
mkdir -pv ${USR_A}/local/cni
CNI_ACI=$(ls ${ACI_PATH}/cni/cni-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/local/cni -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
tar -C ${USR_A}/local/cni -xvf ${CNI_ACI} rootfs/usr --strip 2 ${EXCLUDES}
for p in squashfs-root/bin ${USR_A}/bin
do
    cd ${p}
    ln -svf ../local/cni/bin/cnitool
    cd -
done

HYPERKUBE_ACI=$(ls ${ACI_PATH}/hyperkube/hyperkube-*-linux-amd64.aci | head -n 1)
tar -C squashfs-root/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}
tar -C ${USR_A}/bin -xvf ${HYPERKUBE_ACI} rootfs/ --strip 1 ${EXCLUDES}

cp -v ${ASSETS_DIRECTORY}/enjoliver-agent/serve/enjoliver-agent squashfs-root/bin/
cp -v ${ASSETS_DIRECTORY}/enjoliver-agent/serve/enjoliver-agent ${USR_A}/bin
_upx_in_fs /bin/enjoliver-agent

cp -v ${ASSETS_DIRECTORY}/discoveryC/serve/discoveryC squashfs-root/bin
upx -q squashfs-root/bin/discoveryC
upx -t squashfs-root/bin/discoveryC

for b in /bin/locksmithctl /bin/coreos-cloudinit
do
    _upx_in_fs ${b}
done

mkdir -pv ${USR_A}/local/etc/ squashfs-root/local/etc/
echo -n "{\"release\": \"${VERSION}\", \"alter_timestamp\": \"$(date +%s)\", \"commit\": \"${COMMIT_ID}\"}" | \
    tee ${USR_A}/local/etc/alter-version | tee squashfs-root/local/etc/alter-version

sync

umount ${USR_A}
${COREOS_DIRECTORY}/disk_util --disk_layout=base verity --root_hash=${VERSION_DIR}/coreos_production_image_verity.txt ${VERSION_DIR}/coreos_production_image.bin
printf %s "$(cat ${VERSION_DIR}/coreos_production_image_verity.txt)" | \
        dd of=${BOOT}/coreos/vmlinuz-a conv=notrunc seek=64 count=64 bs=1 status=none
sync

umount ${BOOT}
losetup -d ${LOOP}

${COREOS_DIRECTORY}/disk.py ro
bzip2 -fz ${VERSION_DIR}/coreos_production_image.bin -9

cp -v ${COREOS_DIRECTORY}/coreos-install squashfs-root/bin/coreos-install

mksquashfs squashfs-root/ ../initrd/usr.squashfs -noappend -always-use-fragments
cd ../initrd
find . | cpio -o -H newc | gzip -9 > ../coreos_production_pxe_image.cpio.gz
cd ../

rm -rf squashfs initrd coreos_production_pxe_image.cpio ${USR_A}
