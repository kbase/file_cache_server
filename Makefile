.PHONY: test stress-test

test:
	docker-compose run web sh scripts/run_tests.sh

stress-test:
	docker-compose run web sh -c "python -m unittest test/test_server_stress.py"
