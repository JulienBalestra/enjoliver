#!/dgr/bin/busybox sh

wget -q --spider http://localhost:9200
exit $?
