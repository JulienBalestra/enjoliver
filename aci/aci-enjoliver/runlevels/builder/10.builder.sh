#!/bin/bash

set -ex
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive

### Golang ###
export GOROOT=/usr/local/go
export GOPATH=/go

go version


### PATH ###

ENJOLIVER=${GOPATH}/src/github.com/JulienBalestra/enjoliver
SOURCE_PROJECT=/opt/source-project

mkdir -pv ${ENJOLIVER} ${ROOTFS}/go/src/github.com/JulienBalestra/


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

cd -P ${ENJOLIVER}
pwd -P
git init
git remote add origin ${REMOTE}
git fetch --all
git reset --hard origin/${BRANCH}
git checkout origin/${BRANCH}


### Enjoliver setup ###

export MY_USER=enjoliver
make prod_setup

rm -Rf ${ENJOLIVER}/.git
rm -Rf ${ENJOLIVER}/.ci
rm -Rf ${ENJOLIVER}/aci
rm -Rf ${ENJOLIVER}/chain
rm -Rf ${ENJOLIVER}/discoveryC
rm -Rf ${ENJOLIVER}/docs
rm -Rf ${ENJOLIVER}/hyperkube
rm -Rf ${ENJOLIVER}/py-vendor

find ${ENJOLIVER}/runtime -not -name matchbox -delete || true

chown -R root: ${ENJOLIVER}
mv ${ENJOLIVER} ${ROOTFS}/go/src/github.com/JulienBalestra/