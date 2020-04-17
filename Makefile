PROJECT_NAME = estrade
PYVERSION ?= 3.6.10
POETRY_VERSION ?= 1.0.9
TRAVIS_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
BRANCH_NAME = $(TRAVIS_BRANCH)

DOCKER_CONTAINER_NAME = $(APP_NAME)-$(PYVERSION)
DOCKER_CMD_ENV_VARS = PROJECT_NAME=$(PROJECT_NAME) PYVERSION=$(PYVERSION) BRANCH_NAME=$(BRANCH_NAME)
DOCKER_RUN = $(DOCKER_CMD_ENV_VARS) docker-compose run --rm development
DOCKER_RUN_TESTS_COVERALLS = $(DOCKER_CMD_ENV_VARS) COVERALLS_REPO_TOKEN=$(COVERALLS_REPO_TOKEN) docker-compose run --rm development

BLACK_FOLDERS = $(PROJECT_NAME) tests
ISORT_FOLDERS = $(PROJECT_NAME) tests
FLAKE8_FOLDERS = $(PROJECT_NAME) tests
MYPY_FOLDERS = $(PROJECT_NAME)
RADON_FOLDERS = $(PROJECT_NAME)

PYTEST_OPTIONS = -x -vvv --cov=$(PROJECT_NAME)


shell:
	$(DOCKER_RUN) bash

init:
	docker build --pull \
		--rm \
		-f Dockerfile \
		-t "$(PROJECT_NAME)/dev:$(PYVERSION)" \
		--target development \
		--build-arg IMAGE_NAME="$(PYVERSION)-slim" \
		--build-arg POETRY_VERSION=$(POETRY_VERSION) \
		--build-arg PROJECT_NAME=$(PROJECT_NAME) \
		--build-arg USER_NAME=$(PROJECT_NAME) \
		--build-arg USER_UID=$(shell id -u $$USER) \
		--build-arg USER_GID=$(shell id -g $$USER) \
		.

	# create container and intsall lib
	$(DOCKER_CMD_ENV_VARS) docker-compose run development

test-integration:
	$(DOCKER_RUN) bash -c "poetry run pytest tests/integration/ tests/doc/ $(PYTEST_OPTIONS)"

test-unit:
	$(DOCKER_RUN) bash -c "poetry run pytest tests/unit/ $(PYTEST_OPTIONS)"

test:
	$(DOCKER_RUN) bash -c "poetry run pytest tests/ $(PYTEST_OPTIONS)"

test-report:
	$(DOCKER_RUN) bash -c "poetry run pytest tests/unit/ $(PYTEST_OPTIONS) --cov-report html"

format:
	$(DOCKER_RUN) bash -c "poetry run black $(BLACK_FOLDERS)"
	$(DOCKER_RUN) bash -c "poetry run isort -rc $(ISORT_FOLDERS)"
	$(DOCKER_RUN) bash -c "poetry run radon cc -a -nb $(RADON_FOLDERS)"

style:
	$(DOCKER_RUN) bash -c "poetry run black $(BLACK_FOLDERS) --check --diff"
	$(DOCKER_RUN) bash -c "poetry run flake8 $(FLAKE8_FOLDERS)"
	$(DOCKER_RUN) bash -c "poetry run isort --check-only -rc $(ISORT_FOLDERS)"
	$(DOCKER_RUN) bash -c "poetry run mypy $(MYPY_FOLDERS)"
	$(DOCKER_RUN) bash -c "poetry run xenon --max-absolute B --max-modules A --max-average A $(RADON_FOLDERS)"

docs:
	$(DOCKER_RUN) bash -c "poetry run mkdocs build --clean"

docs-serve:
	$(DOCKER_RUN) bash -c "poetry run mkdocs serve"


pre-commit:
	$(DOCKER_RUN) bash -c "poetry run python scripts/pre-commit.py render-readme"
	$(DOCKER_RUN) bash -c "poetry run python scripts/pre-commit.py docs-requirements"

pre-commit-check:
	$(DOCKER_RUN) bash -c "poetry run python scripts/pre-commit.py render-readme --check-only=1"
	$(DOCKER_RUN) bash -c "poetry run python scripts/pre-commit.py docs-requirements --check-only=1"

ci: style test docs pre-commit-check

clean:
	bash scripts/docker stop_running_containers estrade*
	bash scripts/docker remove_containers estrade*
	bash scripts/docker clean_images estrade*

.PHONY: ci clean docs docs-serve format init pre-commit pre-commit-check shell style test-unit test-integration test-unit test test-report
