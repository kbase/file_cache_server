.PHONY: test test-local stress-test stress-test-local dev-server dev-build

dev-server:
	DEVELOPMENT=1 docker-compose up

dev-build:
	docker-compose down
	docker-compose build --build-arg DEVELOPMENT=1 --no-cache web

test:
	docker-compose run web make test-local

test-local:
	flake8 --max-complexity 5 app.py
	flake8 --max-complexity 5 caching_service
	flake8 test
	mypy --ignore-missing-imports app.py
	mypy --ignore-missing-imports caching_service
	mypy --ignore-missing-imports test
	python -m pyflakes caching_service
	python -m pyflakes app.py
	bandit -r caching_service
	coverage run --source=caching_service -m unittest discover test/caching_service
	coverage report
	coverage html -d coverage_report/
	echo "Generated HTML coverage report to ./coverage_report/index.html"

stress-test:
	docker-compose run web make stress-test-local

stress-test-local:
	python -m unittest test/test_server_stress.py
