#!/usr/bin/env bash

set -e

pylint *.py zoe_* ci/*.py tests/*.py
doc8 docs/
