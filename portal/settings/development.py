from portal.settings.common import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INTERNAL_IPS = ["localhost", "127.0.0.1"]

INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

DEBUG_TOOLBAR_CONFIG = {
    "JQUERY_URL": "",
}

GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ['DB_NAME'],
        "USER": os.environ['DB_USER'],
        "PASSWORD": os.environ['DB_PASSWORD'],
        "HOST": os.environ['DB_HOST'],
        "CHARSET": "utf8",
        "OPTIONS": {"autocommit": True,},
    },
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"file": {"level": "DEBUG", "class": "logging.FileHandler", "filename": BASE_DIR + "/logs/dev.log",},},
    "loggers": {"django": {"handlers": ["file"], "level": "INFO", "propagate": True,}, "django.db.backends": {"handlers": ["file"], "level": "DEBUG",},},
}

AUTHENTICATION_BACKENDS = [
    'freeipa.auth.backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

if  int(env('EMAIL_BACKEND')) == 1:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, "logs")
