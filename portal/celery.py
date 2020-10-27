from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ["django_settings_module"])
app = Celery("portal")
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()
