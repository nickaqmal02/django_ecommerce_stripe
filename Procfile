web: python manage.py migrate --noinput && python manage.py seed_data && gunicorn shopconfig.wsgi:application --bind 0.0.0.0:${PORT:-8000}
