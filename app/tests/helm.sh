#!/usr/bin/env bash

which kubectl > /dev/null
if [ $? -eq 0 ]
then
    KUBECTL=kubectl
else
    KUBECTL="../../hyperkube/hyperkube kubectl"
fi

cd $(dirname $0)

TILLER=$(${KUBECTL} -s 127.0.0.1:8001 get ep -l app=tiller -n kube-system \
    -o jsonpath='{.items[*].subsets[*].addresses[0].ip}:{.items[*].subsets[*].ports[0].port}')
exec ../../runtime/helm/helm --host ${TILLER} $@