#!/usr/bin/env bash 

set -x

cd $(dirname $0)

for p in python3.6 python3.5 python3
do
    ${p} --version && {
    virtualenv env --no-site-packages --system-site-packages -p $(which ${p}) && exit 0
    }
done

exit 2