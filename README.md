Here’s a **clean, professional, and properly formatted `README.md`** version for your **Truck Trip App Backend** — ready to copy directly into your GitHub repository 👇

---

````markdown
# 🚛 Truck Trip App Backend

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Django](https://img.shields.io/badge/Django-5.1.1-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-lightblue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A robust **Django REST API backend** for planning truck trips, incorporating **geocoding**, **route optimization**, **Hours of Service (HOS)** compliance checks, and **automated log sheet generation**.  
Designed for integration with a React frontend, this app leverages **OpenStreetMap (OSM)** for free routing and geocoding, with **GIS-enabled PostgreSQL** for spatial data handling.

---

## ✨ Features

- **Geocoding & Routing:** Converts addresses to coordinates and calculates multi-leg routes using **Nominatim** and **OSRM**.  
- **HOS Compliance:** Validates trips against FMCSA rules (70-hour/8-day cycle, 11-hour daily drive limit, 14-hour on-duty window, 10-hour rest).  
- **Automated Log Sheets:** Generates multi-day ELD-style logs with 24-hour grids (driving, on-duty not driving, off-duty).  
- **Fuel & Rest Stops:** Calculates mandatory stops (e.g., fuel every 1,000 miles, 10-hour rest).  
- **GIS Integration:** Stores locations as PostGIS points for spatial queries.  
- **API-Ready:** JSON responses with route coordinates for easy frontend mapping (e.g., Leaflet/React-Leaflet).  
- **Mac-Optimized Setup:** Tailored for macOS with Homebrew and `virtualenv`.  

---

## 🧩 Prerequisites

- macOS (tested on Ventura+)  
- Python 3.10+  
- PostgreSQL 16+ (via Homebrew)  
- Homebrew (package manager)  
- Git (for cloning)

---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd truck_trip
````

### 2️⃣ Set Up PostgreSQL

Install and start PostgreSQL using Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install postgresql
brew services start postgresql
```

Create the database and user:

```bash
createdb truck_trip_db
# Or via psql:
# psql postgres
# CREATE DATABASE truck_trip_db;
# CREATE USER truck_trip_user WITH PASSWORD 'yourpassword';
# GRANT ALL PRIVILEGES ON DATABASE truck_trip_db TO truck_trip_user;
# \q
```

### 3️⃣ Environment Setup

Install Python and create a virtual environment:

```bash
brew install python@3.12
python3 -m venv django_env
source django_env/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**Pinned Dependencies (`requirements.txt`):**

```text
asgiref==3.8.1
certifi==2024.8.30
cffi==1.17.0
cryptography==43.0.3
Django==5.1.1
djangorestframework==3.15.2
django-cors-headers==5.0.0
geopy==2.4.1
idna==3.10
Pillow==11.2.0
psycopg2-binary==2.9.9
pycparser==2.22
pytz==2024.2
reportlab==4.2.5
requests==2.32.3
sqlparse==0.5.1
typing_extensions==4.12.2
urllib3==2.2.2
```

---

## 🧠 Django Project Initialization

If starting fresh:

```bash
django-admin startproject truck_trip .
python manage.py startapp trips
```

### Update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'truck_trip_db',
        'USER': 'truck_trip_user',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Generate a secret key:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 🧩 Migrations & Server

```bash
python manage.py makemigrations trips
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)** for Django Admin.

---

## 📁 Project Structure

```
truck_trip/
├── manage.py
├── requirements.txt
├── .gitignore
├── truck_trip/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── trips/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
└── README.md
```

---

## 🚀 API Usage

**Base URL:** `/api/`

### **Endpoint:** `POST /api/calculate/`

**Description:**
Calculates a trip route, validates HOS compliance, generates log sheets, and suggests stops.

**Request Example:**

```json
{
  "current_location": {"address": "San Francisco, CA"},
  "pickup_location": {"address": "Los Angeles, CA"},
  "dropoff_location": {"address": "Las Vegas, NV"},
  "current_cycle_used": 20.0
}
```

**Response Example:**

```json
{
  "trip": {
    "id": 1,
    "total_distance": 650.5,
    "total_driving_time": 12.3,
    "logs": [...],
    "created_at": "2025-10-22T10:00:00Z"
  },
  "route_coords": [[37.7749, -122.4194], [34.0522, -118.2437], ...],
  "fuel_stops": [
    {
      "mile": 1000,
      "lat": 35.0,
      "lon": -115.0,
      "type": "Fuel Stop (30 min on-duty not driving)"
    }
  ],
  "rest_stops": [
    {
      "type": "Mandatory 10hr Rest",
      "after_drive_hours": 11,
      "lat": 36.1699,
      "lon": -115.1398
    }
  ],
  "estimated_days": 2
}
```

**Error Response:**

```json
{"error": "Trip exceeds limits: 75.0hrs > 50 remaining, or 9 > 8 days"}
```

**Test with `curl`:**

```bash
curl -X POST http://127.0.0.1:8000/api/calculate/ \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": {"address": "San Francisco, CA"},
    "pickup_location": {"address": "Los Angeles, CA"},
    "dropoff_location": {"address": "Las Vegas, NV"},
    "current_cycle_used": 20
  }'
```

---

## 🌐 CORS Configuration

Pre-configured for React dev (`http://localhost:3000`).
Update `CORS_ALLOWED_ORIGINS` in `settings.py` for production.

---

## ☁️ Deployment

### **Render.com (Recommended)**

1. Push to GitHub.
2. Create a new Web Service on Render.
3. Build command:

   ```bash
   pip install -r requirements.txt
   ```
4. Start command:

   ```bash
   gunicorn truck_trip.wsgi:application
   ```
5. Add environment variables:

   * `SECRET_KEY`
   * `DATABASE_URL` (Render Postgres add-on)
   * `DEBUG=False`
6. Enable PostGIS in DB console.

### **Other Options**

* **Heroku:** use `heroku postgres` and Procfile:

  ```bash
  web: gunicorn truck_trip.wsgi
  ```
* **Vercel/DigitalOcean:** containerized deployment with Docker.

**Example Dockerfile:**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "truck_trip.wsgi:application"]
```

---

## 🤝 Contributing

1. Fork the repo.
2. Create a feature branch:

   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Commit your changes:

   ```bash
   git commit -m 'Add amazing feature'
   ```
4. Push to your branch:

   ```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request.

Report issues via **GitHub Issues** — pull requests welcome!

---

## 🪪 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

## 🧭 Acknowledgments

* **Django & Django REST Framework**
* **PostGIS** for spatial processing
* **OpenStreetMap & OSRM** for free routing/geocoding
* **FMCSA HOS guidelines** for compliance logic

Built with ❤️ for efficient trucking.
Have questions? **Open an issue!**

```

---

Would you like me to also generate a **shorter, professional GitHub repository description (1–2 lines)** for your repo’s sidebar and metadata?
```
