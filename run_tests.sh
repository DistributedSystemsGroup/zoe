#!/usr/bin/env bash

set -e

pylint --ignore old_swarm *.py zoe_*
doc8 docs/

