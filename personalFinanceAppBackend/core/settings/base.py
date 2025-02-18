"""
Django core for personalFinanceAppBackend project.

Generated by 'django-admin startproject' using Django 4.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of core and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_file = BASE_DIR.parent.parent / "env/.env.local.sandbox"

load_dotenv(dotenv_file)


def get_env_value(env_variable, default=""):
    try:
        return os.getenv(env_variable, default)
    except KeyError:
        error_msg = f"Set the {env_variable} environment variable"
        raise ImproperlyConfigured(error_msg)


DEVELOPMENT_MODE = get_env_value("DEVELOPMENT_MODE", "True") == "True"

if not dotenv_file.exists() and DEVELOPMENT_MODE:
    raise ImproperlyConfigured(
        f"Env file {dotenv_file} does not exist while in development mode."
    )

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env_value("DJANGO_DEBUG") == "True"

ALLOWED_HOSTS = get_env_value("DJANGO_ALLOWED_HOSTS", "localhost, 127.0.0.1").split(
    ", "
)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "djoser",
    "social_django",
    "personalFinanceAppBackend.api",
    "personalFinanceAppBackend.users",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Rest framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "personalFinanceAppBackend.users.authentication.CustomJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Djoser Settings
DJOSER = {
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "ACTIVATION_URL": "activation/{uid}/{token}",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "TOKEN_MODEL": None,
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": get_env_value("REDIRECT_URIS").split(", "),
}

# AWS Settings
AWS_ACCESS_KEY_ID = get_env_value("AWS_SES_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_env_value("AWS_SES_SECRET_ACCESS_KEY")
AWS_SES_FROM_EMAIL = get_env_value("AWS_SES_FROM_EMAIL")
USE_SES_V2 = True

# CORS Settings
CORS_ALLOWED_ORIGINS = get_env_value(
    "DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:3000, http://127.0.0.1:3000"
).split(", ")
CORS_ALLOW_CREDENTIALS = True

# CSRF Settings
CSRF_TRUSTED_ORIGINS = get_env_value(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:3000, http://localhost:8000"
).split(", ")

# Auth Cookie Settings
AUTH_COOKIE = "access"
AUTH_REFRESH_COOKIE = "refresh"
AUTH_COOKIE_ACCESS_MAX_AGE = 60 * 0.1
AUTH_COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_REFRESH_PATH = "/auth/jwt/refresh/"
AUTH_COOKIE_SAME_SITE = "None"

# Social Auth Settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = get_env_value("GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = get_env_value("GOOGLE_OAUTH2_SECRET", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["first_name", "last_name"]

SOCIAL_AUTH_FACEBOOK_KEY = get_env_value("FACEBOOK_OAUTH2_KEY", "")
SOCIAL_AUTH_FACEBOOK_SECRET = get_env_value("FACEBOOK_OAUTH2_SECRET", "")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "email, first_name, last_name"}

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "personalFinanceAppBackend.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "personalFinanceAppBackend.core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

if DEVELOPMENT_MODE is True:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": get_env_value("DATABASE_NAME"),
            "USER": get_env_value("DATABASE_USER"),
            "PASSWORD": get_env_value("DATABASE_PASSWORD"),
            "HOST": get_env_value("DATABASE_HOST"),
            "PORT": get_env_value("DATABASE_PORT"),
        }
    }

# Email
EMAIL_BACKEND = "django_ses.SESBackend"
DEFAULT_FROM_EMAIL = get_env_value("AWS_SES_FROM_EMAIL")
DOMAIN = get_env_value("DOMAIN", "localhost:3000")
SITE_NAME = "Gryffen Finance"

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Logging
# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'filename': os.path.join('logs', 'django.log'),
        #     'formatter': 'verbose',
        # },
    },
    "loggers": {
        # This is the root logger that will catch all logs from Django
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
        # This is a specific logger for your app
        "personal_finance_app": {  # Replace with your actual app name
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Plaid Configuration
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_CLIENT_SECRET = os.environ.get("PLAID_CLIENT_SECRET")
