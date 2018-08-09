.PHONY: test publish serve stress_test

test:
	docker-compose run web make test_local

test_local:
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

stress_test:
	docker-compose run web make stress_test_local

stress_test_local:
	python -m unittest test/test_server_stress.py
