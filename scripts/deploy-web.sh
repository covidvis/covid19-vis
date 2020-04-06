#!/usr/bin/env bash

rm -r covidvis.github.io/*
mv website/_site/* covidvis.github.io
pushd covidvis.github.io
git add .
git commit -m "deploy"
git push
popd
