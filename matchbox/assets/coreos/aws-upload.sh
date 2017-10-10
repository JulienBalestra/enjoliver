#!/usr/bin/env bash

# Have a look to this tutorial to get explained steps
# https://bee42.com/de/blog/linuxkit-with-initial-aws-support/

set -ex

cd $(dirname $0)

VERSION=$(readlink serve)
COMMITID=$(git log --pretty=format:'%h' -n 1)

cd ${VERSION}
aws s3 cp coreos_production_image.bin s3://bbc-coreos-container-linux/${VERSION}/${COMMITID}.raw
cd -

cat << EOF > container.json
{
  "Description": "CoreOS Container Linux ${VERSION}:${COMMITID}",
  "Format": "raw",
  "UserBucket": {
    "S3Bucket": "bbc-coreos-container-linux",
    "S3Key": "${VERSION}/${COMMITID}.raw"
  }
}
EOF

aws ec2 import-snapshot --description "BlablaOS" \
    --disk-container file://container.json | tee task-import-snapshot.json

TASKID=$(jq -re .ImportTaskId task-import-snapshot.json)

for i in {0..600}
do
    json=$(aws ec2 describe-import-snapshot-tasks --import-task-ids $TASKID)
    status=$(echo -n $json | jq -re .ImportSnapshotTasks[0].SnapshotTaskDetail.Status)
    if [ ${status} == "completed" ]
    then
        break
    fi
    sleep 10
done


SNAPID=$(aws ec2 describe-import-snapshot-tasks --import-task-ids $TASKID | jq -re .ImportSnapshotTasks[0].SnapshotTaskDetail.SnapshotId)

aws ec2 describe-images --filters "Name=name,Values=BlablaOS-${VERSION}"

set +e
for img in $(aws ec2 describe-images --filters "Name=name,Values=BlablaOS-${VERSION}*" | jq -re .Images[].ImageId)
do
    aws ec2 deregister-image --image-id ${img}
done
set -e

aws ec2 register-image \
    --name "BlablaOS-${VERSION}-${COMMITID}" \
    --architecture x86_64 \
    --virtualization-type hvm \
    --root-device-name /dev/sda1 \
    --block-device-mappings \
    "[{\"DeviceName\": \"/dev/sda1\", \"Ebs\": {\"SnapshotId\": \"${SNAPID}\", \"VolumeType\": \"gp2\"}}]" | tee image-id.json

