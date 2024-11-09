#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Установите максимальное количество попыток
    MAX_ATTEMPTS=30
    ATTEMPTS=0

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
      ATTEMPTS=$((ATTEMPTS + 1))
      if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
        echo "PostgreSQL did not start in time. Exiting."
        exit 1
      fi
    done

    echo "PostgreSQL started"
fi

python manage.py migrate

exec "$@"
