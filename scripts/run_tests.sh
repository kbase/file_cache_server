#!/bin/sh

set -e

flake8 --max-complexity 6 src/caching_service
flake8 src/test
# mypy --ignore-missing-imports src
bandit -r src/caching_service
PYTHONPATH=. pytest -s -vv --cov=src/caching_service --cov-report=term --cov-report=xml src/test/caching_service
