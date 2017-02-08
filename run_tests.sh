#!/usr/bin/env bash

set -e

pylint *.py zoe_*
doc8 docs/

