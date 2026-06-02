#!/bin/sh

# Зупинити виконання скрипту, якщо якась команда завершиться помилкою
set -e


echo "Застосовуємо міграції..."
python manage.py migrate

echo "Збираємо статичні файли (опціонально)..."
# python manage.py collectstatic --noinput

echo "Запускаємо Django сервер..."
exec gunicorn my_project_name.wsgi:application --bind 0.0.0.0:8000 --workers 3