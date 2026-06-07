#!/bin/sh

# Зупинити виконання скрипту, якщо якась команда завершиться помилкою
set -e

echo "Застосовуємо міграції..."
python manage.py migrate

# Створення суперюзера
python manage.py createsuperuser --noinput || true
# альтернатива якщо попередній не працює
#python manage.py shell -c "
#import os
#from django.contrib.auth import get_user_model
#
#User = get_user_model()
#email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
#password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
#
#if email and password:
#    if not User.objects.filter(email=email).exists():
#        User.objects.create_superuser(email=email, password=password)
#        print(f'Superuser {email} created successfully.')
#    else:
#        print(f'Superuser {email} already exists.')
#else:
#    print('Superuser credentials not found in environment variables.')
#"

# Створення дефолтних налаштувань через django shell
python manage.py shell -c "from clinic.models import GlobalClinicSettings; GlobalClinicSettings.objects.get_or_create(singleton_id=1)"

echo "Збираємо статичні файли (опціонально)..."
# python manage.py collectstatic --noinput

echo "Запускаємо Django сервер..."
exec python manage.py runserver 0.0.0.0:8000