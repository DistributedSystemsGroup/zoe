#!/usr/bin/env bash

pylint *.py zoe_* ci/*.py tests/*.py
doc8 docs/
