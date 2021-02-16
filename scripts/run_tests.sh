#!/bin/sh

set -e

flake8 --max-complexity 6 src/caching_service
flake8 src/test
mypy --ignore-missing-imports src
bandit -r src/caching_service
python -m unittest discover src/test/caching_service
