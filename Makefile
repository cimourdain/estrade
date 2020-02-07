SHELL := /bin/bash
VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON_PATH=/usr/bin/python3.6
PYTHON_EXE=python3

DOCKER_RUN = docker-compose run --rm estrade


test: 
	$(DOCKER_RUN) tox --recreate


test-cov:
	( \
		$(VENV_ACTIVATE); \
		pytest --cov=estrade/ --cov-report html tests/ -x; \
		deactivate; \
	)

lint:
	$(DOCKER_RUN) flake8  --max-line-length 120 estrade
