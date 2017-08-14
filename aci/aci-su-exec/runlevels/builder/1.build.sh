#/dgr/bin/busybox sh
VERSION=${ACI_VERSION%-*}
git clone https://github.com/ncopa/su-exec
cd su-exec
git checkout ${VERSION}
make su-exec-static
ls -ll
mkdir -p ${ROOTFS}/bin
mv su-exec-static ${ROOTFS}/bin/su-exec
