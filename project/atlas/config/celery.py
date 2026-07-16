import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("atlas")
# Celery-specific settings are read from Django's settings.py, as long as
# they're prefixed CELERY_ (namespace="CELERY") — one settings file, not two.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Finds a tasks.py in every installed app automatically — no manual
# per-app task registration needed.
app.autodiscover_tasks()
