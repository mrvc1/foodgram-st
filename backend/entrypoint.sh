#!/bin/bash
set -e

echo "Миграции:"
python manage.py makemigrations
python manage.py migrate

echo "Cтатика:"
python manage.py collectstatic --noinput

echo "Ингредиенты:"
python manage.py load_ingredients

echo "Запуск Gunicorn:"
exec gunicorn --bind 0.0.0.0:8000 foodgram.wsgi

