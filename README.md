# That Corporate Flow

A Django operations and client workflow platform.

## Local setup

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

## Deployment

Prepared for Railway deployment.

Required Railway variables:

SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app
DATABASE_URL

Railway start command is handled by Procfile.
