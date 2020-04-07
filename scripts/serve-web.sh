#!/usr/bin/env bash

pushd website
bundle exec jekyll serve
trap "popd" SIGINT
