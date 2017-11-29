#!/usr/bin/env bash

set -e

pylint *.py zoe_* tests/*.py
pytest --ignore integration_tests --tb=short --cov-report=term --cov zoe_api --cov zoe_master --cov zoe_lib

doc8 docs/
sh ./build_docs.sh
