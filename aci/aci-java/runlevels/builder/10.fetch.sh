#!/dgr/bin/busybox sh
.  /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

VERSION=${ACI_VERSION%-*}
JAVA_MAJOR_VERSION=$(echo ${VERSION} | cut -d '.' -f 2)
JAVA_MINOR_VERSION=$(echo ${VERSION} | cut -d '.' -f 3)

PROGRAM_PATH="${ROOTFS}/opt/"
mkdir -p ${PROGRAM_PATH}/jdk${VERSION%.*}

# Download link can be found from http://www.oracle.com/technetwork/java/javase/downloads/index.html
# you have to choose JDK dowload for traget release
# Then Accpet license to get the link. Copy paste it below
JAVA_BUILD_VERSION=$(curl "https://javadl-esd-secure.oracle.com/update/${VERSION%.*}.0/map-m-${VERSION%.*}.0.xml" -s | sed -n 's#.*'${JAVA_MINOR_VERSION}'-\(b[0-9]\+\).*#\1#p' | head -n1)
JAVA_BUILD_HASH=$(curl "https://javadl-esd-secure.oracle.com/update/${VERSION%.*}.0/map-m-${VERSION%.*}.0.xml" -s | sed -n 's#.*/\([a-f0-9]\+\)/au.*#\1#p' |head -n1 )
curl  -j -k -L -H 'Cookie: oraclelicense=accept-securebackup-cookie' \
    "http://download.oracle.com/otn-pub/java/jdk/${JAVA_MAJOR_VERSION}u${JAVA_MINOR_VERSION}-${JAVA_BUILD_VERSION}/${JAVA_BUILD_HASH}/jdk-${JAVA_MAJOR_VERSION}u${JAVA_MINOR_VERSION}-linux-x64.tar.gz" \
    -o jdk.tar.gz

tar -C ${PROGRAM_PATH}/jdk${VERSION%.*} --strip 1 -xzf jdk.tar.gz
rm jdk.tar.gz

[ -f ${PROGRAM_PATH}/jdk${VERSION%.*}/bin/java ]

ln -s /opt/jdk${VERSION%.*}/bin/java ${ROOTFS}/usr/bin/java
ln -s /opt/jdk${VERSION%.*}/bin/java ${ROOTFS}/bin/java
ln -s /opt/jdk${VERSION%.*}/bin/jps  ${ROOTFS}/usr/bin/jps
ln -s /opt/jdk${VERSION%.*}/bin/jps  ${ROOTFS}/bin/jps
