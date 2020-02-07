FROM rcommande/alpine-pyenv

RUN pyenv install 3.6.10
RUN pyenv install 3.7.6
RUN pyenv install 3.8.1
RUN pyenv local 3.6.10 3.7.6 3.8.1

RUN mkdir /estrade
WORKDIR /estrade

# Pipx
RUN sh /entrypoint.sh pip3.8 install pipx
ENV PATH "$PATH:/root/.pyenv/versions/3.8.1/bin/:/root/.local/bin"
RUN pipx ensurepath

# Python tools
RUN pipx install tox
RUN pipx install flake8

