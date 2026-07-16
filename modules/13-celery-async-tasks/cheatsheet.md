# Cheat Sheet — Module 13: Celery & Background/Async Tasks

## The four pieces

- **App** (`config/celery.py`) — knows about your tasks & broker.
- **Broker** (Redis) — the queue; `.delay()` drops a message on it and returns instantly.
- **Worker** (`celery -A config worker`) — separate process, actually runs task code.
- **Beat** (`celery -A config beat`) — separate process, enqueues scheduled tasks on time.

Your Django/web process **never executes task code** — it only enqueues.

## Wiring

```python
# config/celery.py
app = Celery("atlas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()   # finds tasks.py in every installed app
```
```python
# config/__init__.py
from .celery import app as celery_app
__all__ = ("celery_app",)
```

## Writing a task

```python
from celery import shared_task

@shared_task
def send_order_confirmation_email(order_id):   # ID, not an instance — must be JSON-serializable
    from .models import Order                     # local import — models may not be ready yet
    order = Order.objects.select_related("customer").get(pk=order_id)
    ...
```

## Queuing from a signal, safely

```python
@receiver(post_save, sender=Order)
def queue_order_confirmation_email(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(lambda: send_order_confirmation_email.delay(instance.pk))
```
Wrap the multi-step creation that fires the signal in `transaction.atomic()`
too — otherwise `on_commit()` still has nothing complete to wait for.

## Testing — CELERY_TASK_ALWAYS_EAGER

```python
# settings.py
CELERY_TASK_ALWAYS_EAGER = 'pytest' in sys.modules   # NOT an env var set in conftest.py —
                                                       # pytest-django's own django.setup()
                                                       # runs (and caches Celery's config)
                                                       # before your conftest.py body does.
if CELERY_TASK_ALWAYS_EAGER:
    CELERY_RESULT_BACKEND = None
    CELERY_TASK_STORE_EAGER_RESULT = False
```

```python
def test_x(django_capture_on_commit_callbacks, api_client, ...):
    with django_capture_on_commit_callbacks(execute=True):
        api_client.post(...)   # on_commit() callbacks run for real inside this block
```
Without `django_capture_on_commit_callbacks`, `on_commit()` callbacks
never fire in tests — pytest-django rolls back each test's transaction,
and a transaction that never commits never triggers them.

**Rule of thumb:** if a "must happen before X loads" comment describes an
import-order race against a framework that bootstraps itself (pytest,
Django, etc.), don't trust it blindly — detect what's actually running
(`'pytest' in sys.modules`, `sys.argv`) instead of racing the framework's
own startup.

## Scheduling with Beat

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-low-stock-report': {
        'task': 'catalog.tasks.send_low_stock_report',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

## Running it for real

```bash
docker run -p 6379:6379 redis:7
celery -A config worker --loglevel=info    # --pool=solo on Windows
celery -A config beat --loglevel=info
python manage.py runserver
```
