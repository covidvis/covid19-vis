#!/usr/bin/env bash

pushd covidvis.github.io
git pull
rm -r *
mv ../website/_site/* .
git add .
git commit -m "deploy"
git push origin HEAD:master
popd
