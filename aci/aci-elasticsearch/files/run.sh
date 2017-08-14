#!/bin/bash
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

env
/usr/share/elasticsearch/bin/elasticsearch \
    -p \
    /var/run/elasticsearch/elasticsearch.pid \
    -Edefault.path.home=/usr/share/elasticsearch \
    -Edefault.path.logs=/var/log/elasticsearch \
    -Edefault.path.data=/var/lib/elasticsearch \
    -Edefault.path.conf=/etc/elasticsearch \
    -Ebootstrap.system_call_filter=false

retCode=$?
echo "*************** ELASTICSEARCH JAVA PROCESS EXIT $? ******************"
exit ${retCode}
