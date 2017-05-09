#!/usr/bin/env bash

USER_NAME=$1
CERT_FILE=/home/core/kubectl-pki-${USER_NAME}.json

AUTH_OUTPUT=$(vault auth $(/opt/bin/etcdctl --no-sync --endpoints http://127.0.0.1:4002 get /token/kubernetes/kubectl))

if [ $? -ne 0 ]
then
    echo "Vault authentication problem."
    exit 1
fi

JSON_CERTS=$(vault write -format=json pki/kubernetes/issue/kubectl common_name=${USER_NAME})

if [ $? -ne 0 ]
then
    echo "Cannot generate certs."
    exit 2
fi

echo ${JSON_CERTS} | jq .data