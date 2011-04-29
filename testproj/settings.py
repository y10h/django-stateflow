import sys
import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
    }
}


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

# Limit tested apps for jenkins
PROJECT_APPS = (
    'stateflow',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_jenkins',
) + PROJECT_APPS

ODESK_PAYMENT_CLIENT_FACTORY = None
ODESK_API_USER = 'test'
ODESK_PRIVATE_KEY = 'test'
ODESK_PUBLIC_KEY = 'test'
