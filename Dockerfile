FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Обновляем пакетный менеджер
RUN apt-get update -y && apt-get upgrade -y

# Ставим зависимости GDAL, PROJ
RUN apt-get install -y gdal-bin libgdal-dev
RUN apt-get install -y python3-gdal
RUN apt-get install -y binutils libproj-dev

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY ./.pre-commit-config.yaml .

RUN pip install pre-commit
RUN git init
RUN pre-commit install --install-hooks

COPY . /code/
