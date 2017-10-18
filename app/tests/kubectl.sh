#!/usr/bin/env bash

which kubectl > /dev/null
if [ $? -eq 0 ]
then
    KUBECTL=kubectl
else
    KUBECTL="../../hyperkube/hyperkube kubectl"
fi

cd $(dirname $0)
exec ${KUBECTL} --kubeconfig testing_kubeconfig.yaml $@
