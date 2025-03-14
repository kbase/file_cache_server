#!/bin/sh

set -e

flake8 --max-complexity 6 src/caching_service
flake8 src/test
mypy --ignore-missing-imports src
bandit -r src/caching_service
coverage run --source=src/caching_service -m unittest discover src/test/caching_service
coverage report
