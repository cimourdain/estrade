##################################################
#
# Base image
#
##################################################
ARG IMAGE_NAME
FROM python:${IMAGE_NAME} as base

ARG POETRY_VERSION
ARG USER_NAME

##################################################
# ENVIRONMENT VARIABLES
##################################################
# python
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# poetry
ENV POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME="/home/${USER_NAME}/.local/" \
    POETRY_NO_INTERACTION=1

ENV PROJECT_DIRECTORY=/home/${USER_NAME}/app

##################################################
# UPDATE SYSTEM
##################################################
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential \
        # git for coveralls
        git

##################################################
# CREATE USER (based on system user uid/gid)
##################################################
# create user
ARG USER_UID
ARG USER_GID

# Create group if not found in /etc/group
RUN if ! $(awk -F':' '{print $3}' /etc/group |grep -q ${USER_GID}) ; then groupadd -g ${USER_GID} appgroup; fi
# create user
RUN useradd -rm -g ${USER_GID} -G sudo -u ${USER_UID} ${USER_NAME}

USER ${USER_NAME}
WORKDIR ${PROJECT_DIRECTORY}


##################################################
# INSTALL & CONFIGURE POETRY
##################################################
# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python


ENV VENV_PATH="/home/${USER_NAME}/.poetry_cache/virtualenvs"
ENV PATH="${POETRY_HOME}bin:${VENV_PATH}/bin:$PATH"

# configure poetry
RUN poetry config cache-dir "/home/${USER_NAME}/.poetry_cache/"
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project false
RUN poetry config virtualenvs.path "{cache-dir}/virtualenvs"



##################################################
# INSTALL PROJECT DEPENDENCIES (no dev)
##################################################
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev


###################################################
##
## Developement image (used for dev/testing)
##
###################################################
FROM base as development

# install dev dependencies
RUN poetry install
