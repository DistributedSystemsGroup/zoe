#!/usr/bin/env bash

set -e

pylint *.py zoe_* tests/*.py
doc8 docs/
