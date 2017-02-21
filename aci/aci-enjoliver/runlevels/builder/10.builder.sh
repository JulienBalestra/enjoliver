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
export MY_USER=enjoliver
useradd ${MY_USER} -d ${ENJOLIVER}
chown -R ${MY_USER}: ${ENJOLIVER}

make prod_setup

make clean_after_assets

chown -R root: ${ENJOLIVER}

rm -Rf ${ENJOLIVER}/chain
rm -Rf ${ENJOLIVER}/cni
rm -Rf ${ENJOLIVER}/discoveryC
rm -Rf ${ENJOLIVER}/.git

find ${ENJOLIVER}/runtime -not -name matchbox -delete || true

mv ${ENJOLIVER} ${ROOTFS}/opt