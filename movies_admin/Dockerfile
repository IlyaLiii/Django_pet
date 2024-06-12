FROM python:3.10-slim

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
ENV DJANGO_SETTINGS_MODULE 'config.settings'

COPY run_uwsgi.sh run_uwsgi.sh
COPY requirements.txt requirements.txt
COPY uwsgi/uwsgi.ini uwsgi.ini

RUN  apt-get update && apt-get -y install postgresql postgresql-client
RUN  apt-get install --force-yes -y gcc
RUN  apt install --force-yes -y libpq-dev 
RUN  apt-get -y install gettext
RUN  mkdir -p /opt/app/static/
RUN  mkdir -p /opt/app/media/
RUN  pip install --upgrade pip
RUN  pip install -r requirements.txt 

RUN apt install netcat-traditional

COPY . .

RUN  chmod +x ./entrypoint.bash

EXPOSE 8000

ENTRYPOINT ["bash", "./entrypoint.bash"]
