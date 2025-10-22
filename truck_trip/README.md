# Truck Trip App Backend

## Setup

1. Activate venv: source django_env/bin/activate
2. pip install -r requirements.txt
3. Update DATABASES in settings.py with your Postgres creds
4. python manage.py makemigrations
5. python manage.py migrate
6. python manage.py createsuperuser # For admin
7. python manage.py runserver

## API

POST /api/calculate/
Body: {
"current_location": {"address": "Current Addr"},
"pickup_location": {"address": "Pickup Addr"},
"dropoff_location": {"address": "Dropoff Addr"},
"current_cycle_used": 10.5
}

## Deployment

- Render.com: Set env vars for DB, build: pip install -r requirements.txt, start: gunicorn truck_trip.wsgi
