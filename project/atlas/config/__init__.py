# Ensures the Celery app is loaded whenever Django starts, so
# @shared_task-decorated tasks always know which app to register with.
from .celery import app as celery_app

__all__ = ("celery_app",)
