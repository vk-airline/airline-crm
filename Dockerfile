FROM python:3.9

ENV PYTHONUNBUFFERED 1

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt

RUN pip install pre-commit
COPY ./.pre-commit-config.yaml .
RUN git init && pre-commit install --install-hooks

COPY . /code/
