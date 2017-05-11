#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

set -e

npm install -g yarn
