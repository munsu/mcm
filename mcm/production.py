from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['.komadori.xyz']

STATIC_ROOT = '/webapps/mcm_django/static/'

# Set as env vars on the server
TWILIO_SID = None
TWILIO_TOKEN = None
TWILIO_NUMBER = '+15702343621'
