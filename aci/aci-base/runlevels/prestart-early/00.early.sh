#!/dgr/bin/busybox sh
set -e
source /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

DGR_PATH=/dgr

export IP=$(ip addr | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n 1)
export HOSTNAME=`hostname`
#[ ! -z "$DOMAINNAME" ] && FQDN=${HOSTNAME}.${DOMAINNAME} || FQDN=$HOSTNAME

HOST_IP=$(echo ${AC_METADATA_URL} | cut -d '/' -f3 | cut -d ':' -f1)

mkdir -p ${DGR_PATH}/attributes/aci-base
cat > ${DGR_PATH}/attributes/aci-base/prestart.yml <<EOF
default:
  pod:
    hostname: $HOSTNAME
    ip: $IP
  host:
    ip: ${HOST_IP}
EOF
