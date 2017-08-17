#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

set -o pipefail

export LC_ALL=C
export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=$PATH:/go/bin:/usr/local/go/bin


# Fetch sources
WORK_DIR="${GOPATH}/src/k8s.io/kubernetes"
mkdir -p ${WORK_DIR}
curl -sLf "https://github.com/kubernetes/kubernetes/archive/v${ACI_VERSION}.tar.gz" \
    | tar xzf - -C ${WORK_DIR} --strip 1
cd ${WORK_DIR}

# Apply custom patches
PATCHES_DIR="${ACI_HOME}/patches"
for patch in $(ls $PATCHES_DIR)
do
    echo "${PATCHES_DIR}/${patch}"
    head -4 "${PATCHES_DIR}/${patch}"
    patch -p1 < "${PATCHES_DIR}/${patch}" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
    echo ""
done

# If building in a slow travis instance, avoid to be killed by "no logs output since ..."
cat << EOF > tick.sh
#!/bin/bash
until test -x _output/local/go/bin/hyperkube
do
    echo -n "."
    sleep 0.5
done
EOF
chmod +x tick.sh

./tick.sh &

# Build
make hyperkube

# Compress 215MB : 35MB
upx _output/local/go/bin/hyperkube
upx -t _output/local/go/bin/hyperkube

# Small hack to check if the travis instance have enough space
# Keep the current build state for dev rebuild
AVAIL=$(df /dgr/aci-home --output=avail | tail -1)
if [ ${AVAIL} -gt 100000000 ]
then
    cp -v _output/local/go/bin/hyperkube ${ROOTFS}
    cp -v _output/local/go/bin/hyperkube /opt/source-project/hyperkube || true
else
    mv -v _output/local/go/bin/hyperkube ${ROOTFS}
    rm -Rf /go/*
fi

cd -P ${ROOTFS}
./hyperkube --make-symlinks
