"""
Django settings for online_poll_system project (Production Ready)
"""

import os
import secrets
import environ
from pathlib import Path

# --------------------------
# BASE DIRECTORY
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------
# ENVIRONMENT VARIABLES
# --------------------------
env = environ.Env(
    DEBUG=(bool, False),
)

# Load .env file if it exists
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# --------------------------
# SECURITY SETTINGS
# --------------------------
DEBUG = env("DEBUG", default=False)

# SECRET_KEY fallback: .env → env vars → random secret (for CI/Docker)
SECRET_KEY = os.environ.get("SECRET_KEY") or env.str("SECRET_KEY", default=secrets.token_urlsafe(50))


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# --------------------------
# DATABASE
# --------------------------
try:
    DATABASES = {
        "default": env.db(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    }
except Exception:
    # Fallback to SQLite if DATABASE_URL missing/invalid
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --------------------------
# APPLICATION DEFINITION
# --------------------------
INSTALLED_APPS = [
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_yasg",
    "pytest_django",

    # Local apps
    "api.apps.ApiConfig",
    "polls.apps.PollsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files in prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "online_poll_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "online_poll_system.wsgi.application"

# --------------------------
# PASSWORD VALIDATION
# --------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------
# INTERNATIONALIZATION
# --------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------
# STATIC FILES
# --------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------
# MEDIA FILES (Optional)
# --------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

# --------------------------
# REST FRAMEWORK
# --------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# --------------------------
# CACHES
# --------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "polls-cache",
    }
}

# --------------------------
# CUSTOM USER MODEL
# --------------------------
AUTH_USER_MODEL = "api.User"

# --------------------------
# SECURITY BEST PRACTICES
# --------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
X_FRAME_OPTIONS = "DENY"

# --------------------------
# EMAIL CONFIGURATION
# --------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

# --------------------------
# CELERY CONFIGURATION (optional)
# --------------------------
CELERY_ENABLED = env.bool("CELERY_ENABLED", default=False)
if CELERY_ENABLED:
    CELERY_BROKER_URL = env("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
