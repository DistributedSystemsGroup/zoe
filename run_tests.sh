#!/usr/bin/env bash

set -e

pylint *.py zoe_* tests/*.py
pytest --ignore tests --tb=short

doc8 docs/
sh ./build_docs.sh
