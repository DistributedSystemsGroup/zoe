#!/usr/bin/env bash

set -e

rm -Rf dist/ build/ zoe-analytics.egg-info

python3 setup.py sdist

python3 setup.py bdist_wheel

twine upload -r pypi dist/*
