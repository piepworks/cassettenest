import bleach
from pathlib import Path
from environs import Env
import sentry_sdk
from pytz import common_timezones
from django.core.management.utils import get_random_secret_key
from sentry_sdk.integrations.django import DjangoIntegration

env = Env()
# Read .env into os.environ
env.read_env()


sentry_sdk.init(
    dsn=env("SENTRY_DSN", default=None),
    integrations=[
        DjangoIntegration(),
    ],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=env("SENTRY_SAMPLE_RATE"),
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("SECRET_KEY", default=get_random_secret_key())

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Application definition

INSTALLED_APPS = [
    "inventory.apps.InventoryConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_bleach",
    "capture_tag",
    "debug_toolbar",
    "waffle",
    "corsheaders",
    "widget_tweaks",
    "django_htmx",
    "django_browser_reload",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "inventory.middleware.HostnameRedirectMiddleware",
    "inventory.middleware.TimezoneMiddleware",
    "inventory.middleware.MaintenanceModeMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = "film.urls"

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
                "inventory.context_processors.subscription_banner",
            ],
        },
    },
]

WSGI_APPLICATION = "film.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

TIME_ZONES = [(tz, tz) for tz in common_timezones]

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

# Email
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

SUBSCRIPTION_TRIAL = env.bool("SUBSCRIPTION_TRIAL", default=False)
SUBSCRIPTION_TRIAL_DURATION = env("SUBSCRIPTION_TRIAL_DURATION")

# Paddle
PADDLE_LIVE_MODE = env.bool("PADDLE_LIVE_MODE", default=False)
PADDLE_VENDOR_ID = env("PADDLE_VENDOR_ID")
PADDLE_VENDOR_AUTH_CODE = env("PADDLE_VENDOR_AUTH_CODE")
PADDLE_PUBLIC_KEY = env("PADDLE_PUBLIC_KEY")
PADDLE_STANDARD_MONTHLY = env("PADDLE_STANDARD_MONTHLY")
PADDLE_STANDARD_ANNUAL = env("PADDLE_STANDARD_ANNUAL")
PADDLE_AWESOME_ANNUAL = env("PADDLE_AWESOME_ANNUAL")

# Django Debug Toolbar
INTERNAL_IPS = ["127.0.0.1"]

# Allow for checking if someone is logged on via the marketing site.
CORS_ALLOWED_ORIGINS = [env("MARKETING_SITE_URL")]
CORS_ALLOW_METHODS = ["GET"]
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r"^/marketing-site$"

BLEACH_ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.extend(["p", "hr"])

MAINTENANCE_MODE = env.bool("MAINTENANCE_MODE", default=False)

# django-registration
ACCOUNT_ACTIVATION_DAYS = 2
