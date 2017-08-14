#!/dgr/bin/busybox sh
set +e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

mount -o remount,rw /proc/sys || true
/sbin/sysctl --system
mount -o remount,ro /proc/sys || true
exit 0
