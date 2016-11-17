#!/usr/bin/env bash

if [ -z $1 ]
then
    curl -s http://172.20.0.1:5000/discovery/interfaces | jq  ".interfaces [$i][$i].IPv4" | grep -v "127.0.0.1"
    exit 1
fi

KEY=testing.id_rsa

cd $(dirname $0)
ls -l ${KEY}
ssh -i ${KEY} -lcore $1 -o StrictHostKeyChecking=no