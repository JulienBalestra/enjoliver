#!/usr/bin/env bash

SERVER_LIST="control-planes.json"
CERTS_PATH="${HOME}/.kube/certs"

which jq > /dev/null

if [  $# -le 0 ]
then
    echo "Script will connect to each server defined in 'control-planes.json' and generate certs. All files will be saved in ~/.kube/certs directory"
    echo "You must have ssh certs to login to remote cp"
    echo "Usage: $0 user-name"
    echo "  user-name: name for yours certs eg. m.ruszczyk, j.balestra"
    exit 1
fi

if [ $? -ne 0 ]
then
    echo "Need jq to generate certs"
    echo "Use 'apt-get install jq' to install it"
    exit 2
fi

if [ ! -d "${HOME}/.kube/certs" ]
then
    echo "Kube certs directory doesn't exists, creating."
    mkdir -p ~/.kube/certs
fi

while IFS= read -r cp_name &&
      IFS= read -r cp_ip &&
      IFS= read -r cp_username
do
    echo "Getting certs for '${cp_name}' at ${cp_ip}..."
    SSH_OUTPUT=$(ssh ${cp_username}@${cp_ip} "bash -s -l" < create_certs_for_kube_remote.sh $1)

    if [ $? -ne 0 ]
    then
        echo "Operation at remote server failed"
        echo "CERTIFICATES FOR ${cp_name} NOT GENERATED!"
        continue
    fi

    echo ${SSH_OUTPUT} | jq .private_key -r > ${CERTS_PATH}/${cp_name}.priv
    echo ${SSH_OUTPUT} | jq .issuing_ca -r > ${CERTS_PATH}/${cp_name}.isca
    echo ${SSH_OUTPUT} | jq .certificate -r > ${CERTS_PATH}/${cp_name}.cert

    echo "Certifacates for '${cp_name}' saved in ${CERTS_PATH}"

done < <(jq -r '.[] | (.name, .ip, .username)' ${SERVER_LIST})

exit 0
