#!/dgr/bin/busybox sh
.  /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
isLevelEnabled "warning" && set -v
set -e

source /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
version=${ACI_VERSION%-*}

curl -O -sL https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${version}.deb
ES_SKIP_SET_KERNEL_PARAMETERS=true dpkg -i elasticsearch-${version}.deb
rm elasticsearch-${version}.deb
/usr/share/elasticsearch/bin/elasticsearch-plugin install -b https://distfiles.compuscene.net/elasticsearch/elasticsearch-prometheus-exporter-${version}.0.zip
/usr/share/elasticsearch/bin/elasticsearch-plugin install -b repository-s3
/usr/share/elasticsearch/bin/elasticsearch-plugin install -b io.fabric8:elasticsearch-cloud-kubernetes:${version}
