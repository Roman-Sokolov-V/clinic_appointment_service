#!/bin/sh

# Зупинити виконання скрипту, якщо якась команда завершиться помилкою
set -e

echo "Застосовуємо міграції..."
python manage.py migrate

echo "Збираємо статичні файли (опціонально)..."
# python manage.py collectstatic --noinput

echo "Запускаємо Django сервер..."
exec python manage.py runserver 0.0.0.0:8000