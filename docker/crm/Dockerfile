FROM python:3.9

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt install -y netcat

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
