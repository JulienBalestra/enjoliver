#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

apt-get update -q
apt-get install -y -q git python python2.7 bzip2 xz-utils sudo

echo "%sudo ALL=NOPASSWD: ALL" >> /etc/sudoers

mkdir -pv /home/core/repo
useradd core -d /home/core -g sudo -s /bin/bash
chown -R core: /home/core

curl https://storage.googleapis.com/git-repo-downloads/repo > /usr/bin/repo
chmod +x /usr/bin/repo

su - core -c "git config --global user.email \"coreos@enjoliver.local\""
su - core -c "git config --global user.name \"Enjoliver\""

cat << EOF > /home/core/repo/run.sh
#!/bin/bash
repo init -u https://github.com/coreos/manifest.git
repo sync
./chromite/bin/cros_sdk
EOF

chmod +x /home/core/repo/bootstrap.sh
