"""
Django settings for online_poll_system project (Production Ready)
"""
import os
import logging
from pathlib import Path
import environ
import dj_database_url
from datetime import timedelta  
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)
# BASE DIRECTORY
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------
# ENVIRONMENT VARIABLES
# --------------------------
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# ------------------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------------------
DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY", default=None)
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-unsafe-fallback-key"
        logger.warning("Using fallback SECRET_KEY in DEBUG mode.")
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set in production.")
        

ALLOWED_HOSTS = ['codedman.pythonanywhere.com', 'www.codedman.pythonanywhere.com', 'vote-poll.netlify.app', 'www.vote-poll.netlify.app', '127.0.0.1', 'localhost']
# --------------------------
# DATABASES CONFIGURATION
# --------------------------

# CI environment → always use fresh in-memory SQLite
if os.environ.get("CI"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",   # fresh DB for each CI run
        }
    }

# Local development → file-based SQLite
elif os.environ.get("DJANGO_ENV") == "development":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Production → PostgreSQL on Render
else:
    DATABASES = {
        "default": dj_database_url.config(
            default=env("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True,
        )
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
    "rest_framework_simplejwt.token_blacklist",
    "drf_yasg",
    "pytest_django",
    "corsheaders",

    # Local apps
    "api.apps.ApiConfig",
    "polls.apps.PollsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files in production
    "corsheaders.middleware.CorsMiddleware",  # CORS
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
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# --------------------------
# MEDIA FILES (Optional)
# --------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

# --------------------------
# REST FRAMEWORK
# --------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
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


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React frontend local
    "http://127.0.0.1:8000",   # Django local
    "https://vote-online.onrender.com",  # Production domain
    "https://vote-poll.netlify.app",  # frontend domain
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),   # default is 5 minutes
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),      # default is 1 day
}

SWAGGER_USE_COMPAT_RENDERERS = False