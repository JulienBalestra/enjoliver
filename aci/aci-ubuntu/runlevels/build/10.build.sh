#!/dgr/bin/busybox sh
set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export LANG=C
export TERM=xterm
export DEBIAN_FRONTEND=noninteractive

echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/01norecommend
echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/01norecommend

rm -v /etc/resolv.conf

cat << EOF > /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

apt-get update -q
apt-get install -y ca-certificates curl

update-ca-certificates
