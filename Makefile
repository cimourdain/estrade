PYVERSION ?= py36

DOCKER_RUN = docker-compose run --rm estrade-$(PYVERSION)

shell:
	$(DOCKER_RUN) bash

test:
	$(DOCKER_RUN) make test-local

lint:
	$(DOCKER_RUN) make lint-local

docs:
	$(DOCKER_RUN) make docs-local

ci:
	$(DOCKER_RUN) make ci-local


init-local:
	poetry install

test-local: init-local
	poetry run pytest --cov=estrade/ tests/ -x

lint-local: init-local
	poetry run flake8 estrade
	poetry run black estrade -S --check --diff

docs-local: init-local
	poetry run mkdocs build --clean

ci-local: test-local lint-local docs-local
