#!/dgr/bin/busybox sh
set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x


export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

apt-get install -y debootstrap

ln -sfv /usr/share/debootstrap/scripts/gutsy /usr/share/debootstrap/scripts/xenial
debootstrap --arch=amd64 xenial ${ROOTFS} http://archive.ubuntu.com/ubuntu/

rm -Rf  ${ROOTFS}/usr/share/locale/*