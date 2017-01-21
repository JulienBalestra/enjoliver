#!/usr/bin/env bash

set -e

if [ -z "${PRIVATE_REPOSITORY}" ]
then
    echo '${PRIVATE_REPOSITORY}==' "${PRIVATE_REPOSITORY}"
    exit 0
fi

if [ -z "${PUBLIC_REPOSITORY}" ]
then
    echo '${PUBLIC_REPOSITORY}==' "${PUBLIC_REPOSITORY}"
    exit 0
fi

git remote get-url --all origin | grep -c "${PRIVATE_REPOSITORY}" || exit 0
git remote -v

cd -P $(dirname $0)
pwd -P

ssh-keyscan github.com >> githubKey
ssh-keygen -lf githubKey
cat githubKey >> ~/.ssh/known_hosts

echo -n ${HASH} | gpg --passphrase-fd 0 id_rsa.gpg

chmod 400 id_rsa
eval "$(ssh-agent -s)"
ssh-add id_rsa


git remote set-url --push origin "${PUBLIC_REPOSITORY}"
git remote -v
git push origin ${TRAVIS_BRANCH}