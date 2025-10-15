#!/bin/sh
set -e

mkdir -p /app/staticfiles /app/media /app/data

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn ocrsite.wsgi:application --bind 0.0.0.0:8000

