#!/usr/bin/env bash

if [ -z $1 ]
then

    PS3='ssh: '
    options=($(curl -s http://172.20.0.1:5000/discovery/interfaces | \
        jq -r ".interfaces [$i][$i].IPv4" | grep -v "127.0.0.1" | sort))
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