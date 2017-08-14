#!/bin/bash
set -x

echo "### Fix permissions !"

chown elasticsearch. /var/lib/elasticsearch -R
chown elasticsearch. /var/log/elasticsearch -R
mkdir -p /var/run/elasticsearch
chown elasticsearch. /var/run/elasticsearch -R
chmod go+w /tmp
