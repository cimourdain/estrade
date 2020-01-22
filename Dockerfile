ARG image_name
FROM python:$image_name

RUN mkdir /estrade
WORKDIR /estrade

RUN pip install poetry
