FROM python:3.9

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt install -y netcat

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt

RUN pip install pre-commit
COPY ./.pre-commit-config.yaml .
RUN git init
RUN pre-commit install --install-hooks

COPY . /code/
