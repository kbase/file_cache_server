.PHONY: test publish serve stress_test


serve:
	gunicorn -w 2 app:app -b localhost:5000 --reload

test:
	flake8 --max-complexity 5 app.py
	flake8 --max-complexity 5 caching_service
	flake8 test
	mypy --ignore-missing-imports app.py
	mypy --ignore-missing-imports caching_service
	mypy --ignore-missing-imports test
	python -m pyflakes caching_service
	python -m pyflakes app.py
	bandit -r caching_service
	python -m unittest discover test/caching_service

stress_test:
	python -m unittest test/test_server_stress.py
