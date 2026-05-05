import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'your-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'women_safety.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'women_safety.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'profile_pics'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────────
# EMAIL CONFIGURATION  (Gmail SMTP)
# ─────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'shhriyanka.m@gmail.com'
EMAIL_HOST_PASSWORD = 'Shriyanka@12345'
DEFAULT_FROM_EMAIL = 'Women Safety App <shhriyanka.m@gmail.com>'

# ─────────────────────────────────────────────────────────────────
# TWILIO SMS CONFIGURATION
# Sign up free at https://www.twilio.com/try-twilio
# After signup, get these 3 values from https://console.twilio.com
# ─────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID  = 'YOUR_TWILIO_ACCOUNT_SID'   # e.g. AC1234...
TWILIO_AUTH_TOKEN   = 'YOUR_TWILIO_AUTH_TOKEN'     # e.g. 8f3d45...
TWILIO_PHONE_NUMBER = 'YOUR_TWILIO_PHONE_NUMBER'   # e.g. +12345678901
TWILIO_ENABLED      = False   # ← Set to True once you fill in real credentials above
