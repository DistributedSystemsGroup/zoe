#!/usr/bin/env bash

set -e

pylint --ignore old_swarm *.py zoe_* ci
doc8 docs/
