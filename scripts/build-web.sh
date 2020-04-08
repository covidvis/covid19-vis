#!/usr/bin/env bash

pushd website
bundle exec JEKYLL_ENV=production jekyll build
popd
