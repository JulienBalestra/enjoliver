#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

cat << EOF > /etc/apt/sources.list
deb http://fr.archive.ubuntu.com/ubuntu/ xenial main restricted
deb http://fr.archive.ubuntu.com/ubuntu/ xenial multiverse
deb http://fr.archive.ubuntu.com/ubuntu/ xenial universe
deb http://fr.archive.ubuntu.com/ubuntu/ xenial-backports main restricted universe multiverse
deb http://fr.archive.ubuntu.com/ubuntu/ xenial-updates main restricted
deb http://fr.archive.ubuntu.com/ubuntu/ xenial-updates multiverse
deb http://fr.archive.ubuntu.com/ubuntu/ xenial-updates universe
deb http://security.ubuntu.com/ubuntu xenial-security main restricted
deb http://security.ubuntu.com/ubuntu xenial-security multiverse
deb http://security.ubuntu.com/ubuntu xenial-security universe
EOF

apt-get update -qq
apt-get install -y dh-autoreconf cpio squashfs-tools wget libacl1-dev libsystemd-dev \
   pkg-config intltool shtool libcap-dev bison unzip xsltproc build-essential git gperf

TARGET=/tmp/go.tar.gz
curl -L https://storage.googleapis.com/golang/go1.8.3.linux-amd64.tar.gz -o ${TARGET}
tar -C /usr/local -xzf ${TARGET}

export GOROOT=/usr/local/go
export GOPATH=/go

mkdir -pv ${GOPATH}


for b in $(ls ${GOROOT}/bin/ )
do
    ln -sv ${GOROOT}/bin/${b} /usr/local/bin/${b}
done

#echo "deb http://deb.debian.org/debian stretch main" >> /etc/apt/sources.list
#apt-get update -qq
apt-get install -y libmount-dev libmount1


cd /opt

LIBSECCOM_VERSION=2.3.2
curl -Lf https://github.com/seccomp/libseccomp/archive/v${LIBSECCOM_VERSION}.zip -o libseccomp.zip
unzip libseccomp.zip
cd libseccomp-${LIBSECCOM_VERSION}
chmod +x autogen.sh
./autogen.sh
./configure
make
make install

cd /opt


mkdir -pv /go/src/github.com/rkt/rkt

git clone --depth=1 https://github.com/rkt/rkt.git /go/src/github.com/rkt/rkt
cd /go/src/github.com/rkt/rkt


./autogen.sh
./configure --with-stage1-flavors=src,fly \
    --with-stage1-default-flavor=src --with-stage1-systemd-src=https://github.com/kinvolk/systemd.git \
    --with-stage1-systemd-revision=iaguis/pass-fds-pre-post-backport-v234 --with-stage1-systemd-version=v234 \
    --disable-tpm --enable-functional-tests
make

mkdir -pv ${ROOTFS}/usr/lib/rkt/stage1-images/

mv -v build-rkt-*/target/bin/rkt ${ROOTFS}/usr/bin/rkt
mv -v build-rkt-*/target/bin/*.aci ${ROOTFS}/usr/lib/rkt/stage1-images/
