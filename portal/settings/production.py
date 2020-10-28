from .common import *

DEBUG = False

ALLOWED_HOSTS = ["*"]

# email que manda o log dos erros do Django
ADMINS = [("Portal", "marcelo.costa@inpe.br")]

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
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
    "handlers": {"file": {"level": "ERROR", "class": "logging.FileHandler", "filename": BASE_DIR + "/logs/prod.log",},},
    "loggers": {"django": {"handlers": ["file"], "level": "ERROR", "propagate": True,}, "django.db.backends": {"handlers": ["file"], "level": "ERROR",},},
}


AUTHENTICATION_BACKENDS = [
    'freeipa.auth.backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]