#!/bin/bash
set -e
localhost="127.0.0.1"
host="elasticsearch"
port="9200"
cmd="$@"

>&2 echo "!!!!!!!! Check conteiner_a for available !!!!!!!!"
>&2 echo curl http://"$host":"$port"
>&2 echo curl http://"$localhost":"$port"
echo хуйня...
until curl http://"$host":"$port"; do
  >&2 echo "elasticsearch is unavailable - sleeping"
  sleep 1
done

>&2 echo "elasticsearch is up - executing command"

python3 -m postgres_to_es
# if ping -c $ES_SOCKET> /dev/null 2>&1; then
# echo $ES_SOCKET is alive

