"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
APPEND_SLASH=False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


# Application definition

INSTALLED_APPS = [
    'backend.ccm',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'webpack_loader',
    "lti_tool"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'lti_tool.middleware.LtiLaunchMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware'
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.ccm.context_processors.ccm_globals'
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'ccm'),
        'USER': os.getenv('DB_USER', 'admin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'admin'),
        'HOST': os.getenv('DB_HOST', 'ccm_db'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci'
        }
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv('REDIS_LOCATION', "redis://ccm_redis:6379")
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'ccm_web'),
)
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'ccm_web/webpack-stats.json')
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # Gunicorns logging format https://github.com/benoitc/gunicorn/blob/19.x/gunicorn/glogging.py
    'formatters': {
        "generic": {
            "format": "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
        },
    },
    'root': {
        'level': os.getenv('ROOT_LOG_LEVEL', 'INFO'),
        'handlers': ['console']
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'canvas_oauth': {
            'handlers': ['console'],
            'level': 'WARN'
        }
    }
}

# Set CSP_FRAME_SRC to the your Canvas domains
CSP_FRAME_ANCESTORS = ["'self'",] + os.getenv('CSP_FRAME_ANCESTORS', '').split(',')
# This is currently unsafe-inline because of PyLTI scripts. This may be fixed in the future.
CSP_SCRIPT_SRC = ["'self'","'unsafe-inline'", "'unsafe-eval'"] + os.getenv('CSP_SCRIPT_SRC', " ").split(',')
CSP_CONNECT_SRC = ["'self'",] + os.getenv('CSP_SCRIPT_SRC', '').split(',')
CSP_IMG_SRC = ["'self'", "data:"]
CSP_FONT_SRC = ["'self'"]
# Allow inline styles. There are a few styles that come up in the report so it seems easier to just allow unsafe-inline here.
CSP_STYLE_SRC = ["'self'", "https:", "'unsafe-inline'"]


# making LTI launch smooth
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", False)
if CSRF_COOKIE_SECURE:
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Enables Proxies that set headers
    USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', True)

SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", 'None')
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", 'None')
RANDOM_PASSWORD_DEFAULT_LENGTH = os.getenv('RANDOM_PASSWORD_DEFAULT_LENGTH', 32)

# Google Analytics
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', None)
ONE_TRUST_DOMAIN = os.getenv('ONE_TRUST_DOMAIN', None)

HELP_URL = os.getenv('HELP_URL', 'https://ccm.tl-pages.tl.it.umich.edu')

# Canvas URL
CANVAS_INSTANCE_URL = os.getenv('CANVAS_INSTANCE_URL', 'https://canvas.instructure.com')

DEBUGPY_ENABLE = os.getenv('DEBUGPY_ENABLE', False)