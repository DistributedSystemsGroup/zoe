#!/usr/bin/env bash

PYTHONPATH=. sphinx-build -nW -b html -d docs/_build/doctrees docs/ docs/_build/html
