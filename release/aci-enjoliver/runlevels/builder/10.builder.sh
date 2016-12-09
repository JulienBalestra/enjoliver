#!/bin/bash

set -ex
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export DEBIAN_FRONTEND=noninteractive

ENJOLIVER=${ROOTFS}/opt/enjoliver
SOURCE_PROJECT=/opt/source-project


apt-get update
apt-get install -y curl python build-essential python-virtualenv python-dev git file openssh-client tar rsync
ln -vs /usr/lib/python2.7/dist-packages/virtualenv.py /usr/local/bin/virtualenv
chmod +x /usr/local/bin/virtualenv


### CoreOS Baremetal ###
BOOTCFG_VERSION=v0.4.0
BOOTCFG_DIR=${ROOTFS}/usr/bin
BOOTCFG_INSTALL=/opt/bootcfg_install

BOOTCFG=${BOOTCFG_DIR}/bootcfg
BOOTCFG_RELEASE=https://github.com/coreos/coreos-baremetal/releases/download/${BOOTCFG_VERSION}/coreos-baremetal-${BOOTCFG_VERSION}-linux-amd64.tar.gz

mkdir -pv ${BOOTCFG_DIR} ${BOOTCFG_INSTALL}

curl -Lf ${BOOTCFG_RELEASE} -o ${BOOTCFG_INSTALL}/bootcfg.tar.gz
tar -C ${BOOTCFG_INSTALL} -xzf ${BOOTCFG_INSTALL}/bootcfg.tar.gz --strip-components=1
cp -v ${BOOTCFG_INSTALL}/bootcfg ${BOOTCFG}
chmod +x ${BOOTCFG}
${BOOTCFG} --version


### Git Bundle ###
cd -P ${SOURCE_PROJECT}/bundles

HEAD=$(git rev-parse HEAD)
BRANCH=$(git symbolic-ref -q HEAD)
BRANCH=${BRANCH##refs/heads/}
git bundle create ${HEAD}.bundle ${BRANCH} --
git bundle verify ${HEAD}.bundle

git clone ${HEAD}.bundle ${ENJOLIVER}
cd -P ${ENJOLIVER}
git checkout ${BRANCH}


### Golang ###
curl -L https://storage.googleapis.com/golang/go1.7.4.linux-amd64.tar.gz -o /tmp/go1.7.4.linux-amd64.tar.gz
tar -C /usr/local/ -xzvf /tmp/go1.7.4.linux-amd64.tar.gz

export GOROOT=/usr/local/go

for b in $(ls ${GOROOT}/bin/)
do
    ln -s ${GOROOT}/bin/${b} /usr/local/bin/${b}
done

go version


### Enjoliver setup ###

cd -P ${ENJOLIVER}
useradd enjoliver -d ${ENJOLIVER}
chown -R enjoliver ${ENJOLIVER}
su - enjoliver -c "make submodules"

for artifact in lldp/static-aci-lldp-0.aci hyperkube/workspace/hyperkube
do
    su - enjoliver -c "cp -v ${SOURCE_PROJECT}/${artifact} ${ENJOLIVER}/${artifact}"
done

su - enjoliver -c "make assets"
make validate

su - enjoliver -c "make check"
make validate

make check_clean

chown -R root: ${ENJOLIVER}
make validate