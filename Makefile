PYVERSION ?= py36,py37,py38

DOCKER_RUN = docker-compose run --rm estrade

shell:
	$(DOCKER_RUN) ash

test: 
	$(DOCKER_RUN) tox --recreate -e $(PYVERSION)

lint:
	$(DOCKER_RUN) flake8  --max-line-length 120 estrade
