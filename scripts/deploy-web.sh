#!/usr/bin/env bash

# ref: https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/
set -euxo pipefail

WEBDIR=$(realpath website)
DEPLOYDIR=${1:-covidvis.github.io}
BRANCH=${2-master}
if [[ ! -d $DEPLOYDIR ]]; then
    DEPLOYDIR="../${DEPLOYDIR}"
fi
if [[ ! -d $DEPLOYDIR ]]; then
    >&2 echo "Unable to find ${DEPLOYDIR}; please make sure it exists before deploying"
fi
if [[ -z "$(ls -A website/_site)" ]]; then
    make
fi
pushd "${DEPLOYDIR}"
git pull
git rm -r * && rm -rf *
mv "${WEBDIR}"/_site/* .
git add .
git commit -m "deploy"
git push origin $BRANCH
popd
