#!/bin/bash 

cwd=$(dirname $0)
${cwd}/config.py
sudo=""
if [ ${EUID} ]
then
	sudo=sudo
fi
set -x
${sudo} ${cwd}/rkt/rkt --local-config=${cwd} $@
