#!/usr/bin/env bash

set -o pipefail

if [ -z $1 ]
then

    PS3='ssh: '
    options=($(curl -s http://172.20.0.1:5000/discovery/interfaces | \
        jq -re ".[$i].ipv4"  2>/dev/null | sort))
    if [ $? -ne 0 ]
    then
        echo "Fail, try later..."
        exit 2
    fi
    select opt in "${options[@]}"
    do
        IP=$opt
        break
    done
else
    IP=$1
fi

KEY=testing.id_rsa
CMD="sudo -i"

cd $(dirname $0)
echo ${CMD}
until ssh -t -i ${KEY} -lcore ${IP} \
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=1 \
        "${CMD}"
do
    sleep 2
done