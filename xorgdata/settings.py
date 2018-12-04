"""
Django settings for xorgdata project.

Generated by 'django-admin startproject' using Django 2.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import getconf
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config = getconf.ConfigGetter('xorgdata', [
    '/etc/xorgdata/*.ini',
    os.path.join(BASE_DIR, 'local_settings.ini'),
])

APPMODE = config.getstr('app.mode', 'dev')
assert APPMODE in ('dev', 'dist', 'prod'), "Invalid application mode %s" % APPMODE


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.getstr('app.secret_key', 'Dev only!!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.getbool('app.debug', APPMODE == 'dev')

if config.getstr('site.admin_mail'):
    ADMINS = (
        ("XorgData admins", config.getstr('site.admin_mail')),
    )

ALLOWED_HOSTS = config.getlist('site.allowed_hosts', [])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'xorgdata.alumnforce'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'xorgdata.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'xorgdata.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

_ENGINE_MAP = {
    'sqlite': 'django.db.backends.sqlite3',
    'mysql': 'django.db.backends.mysql',
    'postgresql': 'django.db.backends.postgresql_psycopg2',
}
_engine = config.getstr('db.engine', 'sqlite')
if _engine not in _ENGINE_MAP:
    raise ImproperlyConfigured(
        "DB engine %s is unknown; please choose from %s" %
        (_engine, ', '.join(sorted(_ENGINE_MAP.keys())))
    )
if _engine == 'sqlite':
    if APPMODE == 'dev':
        _default_db_name = os.path.join(BASE_DIR, 'dev', 'db.sqlite')
    else:
        _default_db_name = '/var/lib/xorgdata/db.sqlite'
else:
    _default_db_name = 'xorgdata'

DATABASES = {
    'default': {
        'ENGINE': _ENGINE_MAP[_engine],
        'NAME': config.getstr('db.name', _default_db_name),
        'USER': config.getstr('db.user'),
        'PASSWORD': config.getstr('db.password'),
        'HOST': config.getstr('db.host', 'localhost'),
        'PORT': config.getstr('db.port'),
    },
}

if _engine == 'mysql':
    # Detect data integrity problems in MySQL early
    # https://django-mysql.readthedocs.io/en/latest/checks.html#django-mysql-w001-strict-mode
    DATABASES['default']['OPTIONS'] = {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

EMAIL_HOST = config.getstr("email.host")
EMAIL_PORT = config.getint("email.port")
EMAIL_HOST_USER = config.getstr("email.user")
EMAIL_HOST_PASSWORD = config.getstr("email.password")
EMAIL_USE_TLS = config.getbool("email.tls")
DEFAULT_FROM_EMAIL = config.getstr("email.default_from_email", "Polytechnique.org <noreply@polytechnique.org>")
SERVER_EMAIL = config.getstr("email.server_email", "Polytechnique.org <noreply@polytechnique.org>")
EMAIL_SUBJECT_PREFIX = config.getstr('email.subject_prefix', '[Django xorgdata]') + ' '

# In development mode, send messages to the console
if APPMODE == 'dev':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

USE_HTTPS = (APPMODE == 'prod') or config.getbool("security.use_ssl")
SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS

if USE_HTTPS:
    # Force using HSTS with HTTPS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = config.getint('security.hsts_seconds', 15768000)
