SHELL := /bin/bash
VENV_NAME?=.venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON_PATH=/usr/bin/python3.6
PYTHON_EXE=python3



install: 
	( \
		rm -rf $(VENV_NAME)/; \
		$(PYTHON_EXE) -m virtualenv $(VENV_NAME) -p $(PYTHON_PATH); \
		$(VENV_ACTIVATE); \
		echo "${VIRTUAL_ENV}"; \
		pip list; \
		pip install -r requirements.txt; \
		pip list; \
		deactivate; \
	)

install-dev: install
	( \
		$(VENV_ACTIVATE); \
		pip install -r requirements-dev.txt; \
		pip list; \
		deactivate; \
	)

test: 
	( \
		$(VENV_ACTIVATE); \
		pytest tests/ -x --log-level=DEBUG; \
		deactivate; \
	)

test-cov:
	( \
		$(VENV_ACTIVATE); \
		pytest --cov=estrade/ --cov-report html tests/ -x; \
		deactivate; \
	)

lint:
	( \
		$(VENV_ACTIVATE); \
		flake8  --max-line-length 120 estrade/ ; \
		deactivate; \
	)
