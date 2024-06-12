FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN  apt-get update && apt-get -y install postgresql postgresql-client
RUN  apt install --force-yes -y libpq-dev 
RUN  apt-get install --force-yes -y gcc
RUN  pip install --upgrade pip
RUN  pip install -r requirements.txt
RUN apt install --force-yes -y curl
COPY . .

RUN  chmod +x ./entrypoint.bash

# HEALTHCHECK --interval=5s --timeout=10s --retries=3 CMD curl -sS 127.0.0.1:9200 || exit 1

ENTRYPOINT ["bash", "./entrypoint.bash"]
