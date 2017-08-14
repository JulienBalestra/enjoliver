#!/bin/bash
set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

[ $(ls -1  /dgr/builder/runlevels/build |wc -l ) -eq 0 ] && exit 0
[ ! -z ${APT_PROXY} ] && rm -f /etc/apt/apt.conf.d/01proxy
echo_green '==== Cleaning rootfs from packages ===='
apt-get autoremove --purge -y
apt-get clean
echo_green '==== Cleaning TMP dir ===='
rm -rf /tmp/*


echo_green '==== Cleaning rootfs ===='
find / -prune -name '*.deb' -exec rm {} \;
for logfile in $(find / -prune -name '*.log')
 do
   > $logfile
 done
for rootdir in /var/lib/apt/lists/ \
               /usr/share/doc \
               /usr/share/man; do
  find ${rootdir} -prune -type f -exec rm {} \;
 done
rm -f  /var/cache/apt/*.bin
rm -Rf /var/lib/apt/lists/*