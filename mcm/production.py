from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['.komadori.xyz']

STATIC_ROOT = '/webapps/mcm_django/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mcm',
        'USER': 'mcm',
        'PASSWORD': os.getenv('PSQL_PASSWORD'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Set as env vars on the server
TWILIO_SID = None
TWILIO_TOKEN = None
TWILIO_NUMBER = '+15702343621'
TWILIO_NUMBER2 = '+16467988133'
