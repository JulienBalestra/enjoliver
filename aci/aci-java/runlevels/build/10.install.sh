#!/dgr/bin/busybox sh
.  /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

ln -s /opt/jdk1.8/bin/java /usr/bin/java
ln -s /opt/jdk1.8/bin/java /bin/java
ln -s /opt/jdk1.8/bin/jps /usr/bin/jps
ln -s /opt/jdk1.8/bin/jps /bin/jps
