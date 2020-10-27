from .common import *

DEBUG = False

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",}}

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "logs")


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
