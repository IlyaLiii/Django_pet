#!/bin/bash
set -e

# Придумаю, как сделать, пока просто заслипаю не короткое время
# while true; netcat -z $DB_HOST $DB_PORT; do
# echo "Whait DB..."
# sleep 0.1
# done

echo "Whait DB..."
sleep 3

psql -h $DB_HOST -U $DB_USER -f ../schema.ddl


# python manage.py migrate --noinput # выполнение миграций
# python ../sqlite_to_postgres/load_data.py # загрузка данных в базу
# python manage.py compilemessages -l en -l ru 
# python manage.py collectstatic -c --noinput
# python manage.py shell -c "exec(open('scripts/create_base_superuser.py').read())"
uwsgi --strict --ini uwsgi.ini


