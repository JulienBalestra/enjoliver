#!/bin/bash
# Copyright (c) 2013 The CoreOS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e -o pipefail

error_output() {
    echo "Error: return code $? from $BASH_COMMAND" >&2
}

# Ensure that required executables exist before proceeding
which wget >/dev/null || { echo 'Missing wget!' >&2 ; exit 1 ; }
which gpg >/dev/null || { echo 'Missing gpg!' >&2 ; exit 1 ; }

# Everything we do should be user-access only!
umask 077

if grep -q "^ID=coreos$" /etc/os-release; then
    source /etc/os-release
    [[ -f /usr/share/coreos/update.conf ]] && source /usr/share/coreos/update.conf
    [[ -f /etc/coreos/update.conf ]] && source /etc/coreos/update.conf
fi

# Fall back on the current stable if os-release isn't useful
: ${VERSION_ID:=current}
CHANNEL_ID=${GROUP:-stable}

OEM_ID=
if [[ -e /etc/oem-release ]]; then
    # Pull in OEM information too, but prefixing variables with OEM_
    eval "$(sed -e 's/^/OEM_/' /etc/oem-release)"
fi

USAGE="Usage: $0 [-V version] [-d /dev/device]
Options:
    -d DEVICE   Install CoreOS to the given device.
    -V VERSION  Version to install (e.g. current) [default: ${VERSION_ID}]
    -C CHANNEL  Release channel to use (e.g. beta) [default: ${CHANNEL_ID}]
    -o OEM      OEM type to install (e.g. ami) [default: ${OEM_ID:-(none)}]
    -c CLOUD    Insert a cloud-init config to be executed on boot.
    -i IGNITION Insert an Ignition config to be executed on boot.
    -t TMPDIR   Temporary location with enough space to download images.
    -v          Super verbose, for debugging.
    -b BASEURL  URL to the image mirror
    -n          Copy generated network units to the root partition.
    -h          This ;-)

This tool installs CoreOS on a block device. If you PXE booted CoreOS on a
machine then use this tool to make a permanent install.
"

# Image signing key:
# pub   4096R/93D2DCB4 2013-09-06
# uid       [ unknown] CoreOS Buildbot (Offical Builds) <buildbot@coreos.com>
# sub   4096R/74E7E361 2013-09-06 [expired: 2014-09-06]
# sub   4096R/E5676EFC 2014-09-08 [expired: 2015-09-08]
# sub   4096R/1CB5FA26 2015-08-31 [expires: 2017-08-30]
# sub   4096R/B58844F1 2015-11-20 [revoked: 2016-05-16]
# sub   4096R/2E16137F 2016-05-16 [expires: 2017-05-16]
GPG_LONG_ID="50E0885593D2DCB4"
GPG_KEY="-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2
<truncate/>
-----END PGP PUBLIC KEY BLOCK-----
"

DEVICE=""
CLOUDINIT=""

while getopts "V:C:d:o:c:i:t:b:nvh" OPTION
do
    case $OPTION in
        V) VERSION_ID="$OPTARG" ;;
        C) CHANNEL_ID="$OPTARG" ;;
        d) DEVICE="$OPTARG" ;;
        o) OEM_ID="$OPTARG" ;;
        c) CLOUDINIT="$OPTARG" ;;
        i) IGNITION="$OPTARG" ;;
        t) export TMPDIR="$OPTARG" ;;
        v) set -x ;;
        b) BASE_URL="$OPTARG" ;;
        n) COPY_NET=1;;
        h) echo "$USAGE"; exit;;
        *) exit 1;;
    esac
done

# Device is required, must not be a partition, must be writable
if [[ -z "${DEVICE}" ]]; then
    echo "$0: No target block device provided, -d is required." >&2
    exit 1
fi

if ! [[ $(lsblk -n -d -o TYPE "${DEVICE}") =~ ^(disk|loop|lvm)$ ]]; then
    echo "$0: Target block device (${DEVICE}) is not a full disk." >&2
    exit 1
fi

if [[ ! -w "${DEVICE}" ]]; then
    echo "$0: Target block device (${DEVICE}) is not writable (are you root?)" >&2
    exit 1
fi

if [[ -n "${CLOUDINIT}" ]]; then
    if [[ ! -f "${CLOUDINIT}" ]]; then
        echo "$0: Cloud config file (${CLOUDINIT}) does not exist." >&2
        exit 1
    fi

    if type -P coreos-cloudinit >/dev/null; then
        if ! coreos-cloudinit -from-file="${CLOUDINIT}" -validate; then
            echo "$0: Cloud config file (${CLOUDINIT}) is not valid." >&2
            exit 1
        fi
    else
        echo "$0: coreos-cloudinit not found. Could not validate config. Continuing..." >&2
    fi
fi

if [[ -n "${IGNITION}" ]]; then
    if [[ ! -f "${IGNITION}" ]]; then
        echo "$0: Ignition config file (${IGNITION}) does not exist." >&2
        exit 1
    fi
fi

if [[ -n "${OEM_ID}" ]]; then
    IMAGE_NAME="coreos_production_${OEM_ID}_image.bin.bz2"
else
    IMAGE_NAME="coreos_production_image.bin.bz2"
fi

# for compatibility with old versions that didn't support channels
if [[ "${VERSION_ID}" =~ ^(alpha|beta|stable)$ ]]; then
    CHANNEL_ID="${VERSION_ID}"
    VERSION_ID="current"
fi

if [[ -z "${BASE_URL}" ]]; then
    BASE_URL="https://${CHANNEL_ID}.release.core-os.net/amd64-usr"
fi

# if the version is "current", resolve the actual version number
if [[ "${VERSION_ID}" == "current" ]]; then
    VERSION_ID=$(wget --quiet -O - "${BASE_URL}/${VERSION_ID}/version.txt" | \
        gawk --field-separator '=' '/COREOS_VERSION=/ { print $2 }')
    echo "Current version of CoreOS ${CHANNEL_ID} is ${VERSION_ID}"
fi

IMAGE_URL="${BASE_URL}/${VERSION_ID}/${IMAGE_NAME}"
SIG_NAME="${IMAGE_NAME}.sig"
SIG_URL="${BASE_URL}/${VERSION_ID}/${SIG_NAME}"

if ! wget --spider --quiet "${IMAGE_URL}"; then
    echo "$0: Image URL unavailable: $IMAGE_URL" >&2
    exit 1
fi

if ! wget --spider --quiet "${SIG_URL}"; then
    echo "$0: Image signature unavailable: $SIG_URL" >&2
    exit 1
fi

# Pre-flight checks pass, lets get this party started!
WORKDIR=$(mktemp --tmpdir -d coreos-install.XXXXXXXXXX)
trap "error_output ; rm -rf '${WORKDIR}'" EXIT

# Setup GnuPG for verifying the image signature
export GNUPGHOME="${WORKDIR}/gnupg"
mkdir "${GNUPGHOME}"
gpg --batch --quiet --import <<<"$GPG_KEY"

echo "Downloading the signature for ${IMAGE_URL}..."
wget --no-verbose -O "${WORKDIR}/${SIG_NAME}" "${SIG_URL}"

# We are at the point of no return, so wipe disk labels that are missed below.
# In particular, ZFS writes labels in the last half-MiB of the disk.
dd if=/dev/zero of="${DEVICE}" count=1024 2>/dev/null \
    seek=$(($(blockdev --getsz "${DEVICE}") - 1024))

echo "Downloading, writing and verifying ${IMAGE_NAME}..."
declare -a EEND
if ! wget --no-verbose -O - "${IMAGE_URL}" \
    | tee >(bunzip2 --stdout >"${DEVICE}") \
    | gpg --batch --trusted-key "${GPG_LONG_ID}" \
        --verify "${WORKDIR}/${SIG_NAME}" -
then
    EEND=(${PIPESTATUS[@]})
    [ ${EEND[0]} -ne 0 ] && echo "${EEND[0]}: Download of ${IMAGE_NAME} did not complete" >&2
    [ ${EEND[1]} -ne 0 ] && echo "${EEND[1]}: Cannot expand ${IMAGE_NAME} to ${DEVICE}" >&2
    [ ${EEND[2]} -ne 0 ] && echo "${EEND[2]}: GPG signature verification failed for ${IMAGE_NAME}" >&2
    wipefs --all --backup "${DEVICE}"
    exit 1
fi

# inform the OS of partition table changes
udevadm settle
for try in 0 1 2 4; do
    sleep "$try"  # Give the device a bit more time on each attempt.
    blockdev --rereadpt "${DEVICE}" && unset try && break ||
    echo "Failed to reread partitions on ${DEVICE}" >&2
done
[ -z "$try" ] || exit 1

if [[ -n "${CLOUDINIT}" ]] || [[ -n "${COPY_NET}" ]]; then
    # The ROOT partition should be #9 but make no assumptions here!
    # Also don't mount by label directly in case other devices conflict.
    ROOT_DEV=$(blkid -t "LABEL=ROOT" -o device "${DEVICE}"*)

    mkdir -p "${WORKDIR}/rootfs"
    case $(blkid -t "LABEL=ROOT" -o value -s TYPE "${ROOT_DEV}") in
      "btrfs") mount -t btrfs -o subvol=root "${ROOT_DEV}" "${WORKDIR}/rootfs" ;;
      *)       mount "${ROOT_DEV}" "${WORKDIR}/rootfs" ;;
    esac
    trap "error_output ; umount '${WORKDIR}/rootfs' && rm -rf '${WORKDIR}'" EXIT

    if [[ -n "${CLOUDINIT}" ]]; then
      echo "Installing cloud-config..."
      mkdir -p "${WORKDIR}/rootfs/var/lib/coreos-install"
      cp "${CLOUDINIT}" "${WORKDIR}/rootfs/var/lib/coreos-install/user_data"
    fi

    if [[ -n "${COPY_NET}" ]]; then
      echo "Copying network units to root partition."
      # Copy the entire directory, do not overwrite anything that might exist there, keep permissions, and copy the resolve.conf link as a file.
      cp --recursive --no-clobber --preserve --dereference /run/systemd/network/* "${WORKDIR}/rootfs/etc/systemd/network"
    fi

    umount "${WORKDIR}/rootfs"
    trap "error_output ; rm -rf '${WORKDIR}'" EXIT
fi

if [[ -n "${IGNITION}" ]]; then
    # The OEM partition should be #6 but make no assumptions here!
    # Also don't mount by label directly in case other devices conflict.
    OEM_DEV=$(blkid -t "LABEL=OEM" -o device "${DEVICE}"*)

    mkdir -p "${WORKDIR}/oemfs"
    mount "${OEM_DEV}" "${WORKDIR}/oemfs"
    trap "error_output ; umount '${WORKDIR}/oemfs' && rm -rf '${WORKDIR}'" EXIT

    echo "Installing Ignition config ${IGNITION}..."
    cp "${IGNITION}" "${WORKDIR}/oemfs/coreos-install.json"
    echo  "set linux_append=\"coreos.config.url=oem:///coreos-install.json\"" > "${WORKDIR}/oemfs/grub.cfg"

    umount "${WORKDIR}/oemfs"
    trap "error_output ; rm -rf '${WORKDIR}'" EXIT
fi

rm -rf "${WORKDIR}"
trap - EXIT

echo "Success! CoreOS ${CHANNEL_ID} ${VERSION_ID}${OEM_ID:+ (${OEM_ID})} is installed on ${DEVICE}"