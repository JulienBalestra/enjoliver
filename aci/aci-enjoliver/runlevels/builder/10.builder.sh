#!/bin/bash

set -ex
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

ENJOLIVER=/opt/enjoliver
SOURCE_PROJECT=/opt/source-project


### Git Bundle ###
if [ -d ${SOURCE_PROJECT}/bundles ]
then
    cd -P ${SOURCE_PROJECT}/bundles

    HEAD=$(git rev-parse HEAD)

    # If in a detached HEAD symbolic-ref fail -> Fix before by reattach it in a new branch
    BRANCH=$(git symbolic-ref -q HEAD --short)
    git bundle create ${HEAD}.bundle ${BRANCH} --
    git bundle verify ${HEAD}.bundle
    REMOTE=${SOURCE_PROJECT}/bundles/${HEAD}.bundle
else
    REMOTE=https://github.com/JulienBalestra/enjoliver.git
    BRANCH=master
fi

mkdir -pv ${ENJOLIVER}
cd -P ${ENJOLIVER}
pwd -P
git init
git remote add origin ${REMOTE}
git fetch --all
git reset --hard origin/${BRANCH}
git checkout origin/${BRANCH}


### Golang ###
GOROOT=/usr/local/go
go version


### Enjoliver setup ###

cd -P ${ENJOLIVER}
useradd enjoliver -d ${ENJOLIVER}
chown -R enjoliver ${ENJOLIVER}
su - enjoliver -c "make submodules"
su - enjoliver -c "make runner"
su - enjoliver -c "make front"
su - enjoliver -c "make pip"

su - enjoliver -c "make assets"
make clean_after_assets
make validate

chown -R root: ${ENJOLIVER}

mv ${ENJOLIVER} ${ROOTFS}/opt