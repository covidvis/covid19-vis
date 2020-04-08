#!/usr/bin/env bash

pushd website
JEKYLL_ENV=production bundle exec jekyll build
popd
