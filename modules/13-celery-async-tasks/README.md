# Module 13 — Celery & Background/Async Tasks

> **Where we're going:** some work shouldn't happen while a user waits for a
> response — sending an email, generating a report. We wire Celery into
> Atlas so that work runs on a separate worker process, off the
> request/response cycle entirely, and we schedule a recurring job with
> Celery Beat. Along the way we hit — and fix — a real, subtle bug in how
> async code gets tested, which teaches more about import order and
> process startup than any contrived example could.

## 1. The problem: slow work inside the request/response cycle

Right now, if `OrderSerializer.create()` sent a confirmation email
directly, the customer's browser would sit waiting on the *entire* email
send (DNS lookup, SMTP handshake, whatever a flaky mail provider decides
to do that day) before it got its `201 Created` response. Multiply that by
every customer placing an order at once, and every request-handling
process (there are only so many) is tied up waiting on mail servers
instead of serving requests.

The fix: hand the email off to something else, and respond to the browser
immediately. That "something else" is Celery — **a separate worker
process** that pulls jobs off a queue and runs them independently of any
web request.

## 2. The mental model: app, broker, worker, beat

Four moving pieces:

- **The Celery app** (`config/celery.py`) — the object that knows about
  your tasks and how to talk to a broker. One per project.
- **The broker** — Redis here — a message queue. Calling a task's
  `.delay()` doesn't run it; it drops a message ("run task X with these
  arguments") onto the broker and returns instantly.
- **The worker** (`celery -A config worker`) — a long-running separate
  process that watches the broker, pulls messages off it, and actually
  executes the task function, whenever it gets to it.
- **Beat** (`celery -A config beat`) — a scheduler process that drops
  messages onto the broker on a timer (e.g. "run the low-stock report
  every day at 8am"), instead of a person remembering to run it.

Your Django process (`runserver`, Gunicorn, whatever serves requests)
**never runs task code itself** — it only ever enqueues messages. That
decoupling is the entire point: a slow task can't slow down a request.

## 3. Wiring Celery into Django

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("atlas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

`config_from_object(..., namespace="CELERY")` means every setting in
`settings.py` prefixed `CELERY_` becomes a Celery config option — one
settings file, not two. `autodiscover_tasks()` finds a `tasks.py` in every
installed app automatically, so `orders/tasks.py` and `catalog/tasks.py`
both get picked up with zero manual registration.

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ("celery_app",)
```

This import has to live in `config/__init__.py` specifically — it runs
the moment *anything* imports the `config` package (which happens for
every Django process), guaranteeing `@shared_task`-decorated functions
always have an app to register with, whether that process is a web
worker, a Celery worker, or a test run.

## 4. Writing a task

```python
# orders/tasks.py
from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_order_confirmation_email(order_id):
    from .models import Order  # local import: avoids loading models before Django apps are ready

    order = Order.objects.select_related("customer").get(pk=order_id)
    send_mail(
        subject=f"Atlas order #{order.pk} confirmation",
        message=(
            f"Hi {order.customer.full_name},\n\n"
            f"Thanks for your order #{order.pk} — total ${order.total}.\n"
            f"Status: {order.get_status_display()}."
        ),
        from_email=None,
        recipient_list=[order.customer.email],
    )
    return f"Sent confirmation for order {order.pk} to {order.customer.email}"
```

Two details that matter for every Celery task you'll ever write, not just
this one:

- **Takes an ID, not a model instance.** Task arguments get serialized
  (JSON, per `CELERY_TASK_SERIALIZER`) to travel through the broker to a
  worker that might be a different process entirely — a live Python
  object can't cross that boundary, and even if it somehow could, it'd
  carry stale data by the time the worker actually runs. Always look the
  object up fresh, by ID, inside the task.
- **Local import of the model.** Task modules get imported very early
  (via `autodiscover_tasks()`, while Django apps are still loading) —
  importing models at the top of `tasks.py` risks running before the app
  registry is ready.

## 5. Triggering a task, and the bug it was designed to avoid

The naive way to queue this: call `.delay()` right in the view or
serializer after saving. Atlas does it via a signal instead —
`post_save` on `Order` — which decouples "an order was created" from "who
needs to react to that."

```python
# orders/signals.py
@receiver(post_save, sender=Order)
def queue_order_confirmation_email(sender, instance, created, **kwargs):
    if not created:
        return  # only on INSERT — an update (e.g. status -> "paid") shouldn't resend it

    transaction.on_commit(lambda: send_order_confirmation_email.delay(instance.pk))
```

```python
# orders/apps.py
class OrdersConfig(AppConfig):
    name = 'orders'

    def ready(self):
        from . import signals  # noqa: F401 — import registers the @receiver hooks
```

Here's the subtlety `transaction.on_commit()` exists to solve.
`OrderSerializer.create()` creates the `Order` row first, then loops to
create each `OrderItem` — and `post_save` fires the **instant** the
`Order` row is inserted, before any `OrderItem` exists. Queue the task
immediately and a worker (or, in eager tests, this exact line) could run
against an order with **zero items**, computing a $0.00 total. The fix
needed two matching pieces:

```python
# orders/serializers.py — create() now wrapped in atomic()
def create(self, validated_data):
    with transaction.atomic():
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
    return order
```

`transaction.atomic()` groups the `Order` and every `OrderItem` into one
transaction. `transaction.on_commit()` defers the task-queueing lambda
until that *entire* transaction actually commits — which is also the
general-purpose reason to always queue Celery tasks this way in real
systems: without it, a fast worker can beat an in-progress transaction to
the database and find nothing there at all.

## 6. Testing async code — and a real bug this module hit

The obvious approach: set `CELERY_TASK_ALWAYS_EAGER = True` for tests, so
`.delay()` runs the task synchronously, in-process, no broker needed.

The **first** attempt at wiring this up looked reasonable and was wrong
in a way that only showed up on `.delay()`, not on direct calls:

```python
# conftest.py — THE BROKEN VERSION
import os
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")  # "before Django settings load"...
import pytest
...
```

```python
# settings.py — THE BROKEN VERSION
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False') == 'True'
```

Running the suite: 43 tests passed, and exactly the two tests that
actually called `.delay()` (not a direct function call) failed — each
one burning ~20 seconds retrying a connection to a Redis server that
was never running, then raising `RuntimeError: Retry limit exceeded`.

The comment's premise ("before Django settings load — including by
pytest-django itself") turned out to be false. Reproduced directly:

```python
django.setup()                                  # what pytest-django does in ITS OWN
                                                 # pytest_configure hook — before your
                                                 # project's root conftest.py ever runs
import os
os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'True'  # what conftest.py does — too late
from config.celery import app
print(app.conf.task_always_eager, app.conf.result_backend)
# False redis://localhost:6379/0    <- locked in, permanently, for the rest of the process
```

`pytest-django` calls `django.setup()` — which populates every app,
including `orders`' `AppConfig.ready()`, which imports `orders.signals`,
which imports `orders.tasks`, which builds Celery's config — **before**
the project's own root `conftest.py` module body ever executes. Celery
caches its resolved config the first time it's read. By the time
`conftest.py` set the env var, it was already too late; `.delay()` for
the rest of that process talked to a real (absent) Redis server, while
every test calling task functions **directly** (bypassing Celery
entirely) never noticed anything wrong.

The fix drops the env-var timing dependency altogether:

```python
# settings.py — THE FIX
CELERY_TASK_ALWAYS_EAGER = 'pytest' in sys.modules
```

This isn't sensitive to *when* `settings.py` happens to run, because it
doesn't depend on anything happening first — `pytest` necessarily imports
**itself** before it can call any hook at all, so `'pytest' in
sys.modules` is already `True` the very first time `settings.py`
executes under pytest, no matter how early in the process that is.
`conftest.py` no longer needs to set anything.

The lesson generalizes well past Celery: a "do X before Django/pytest
loads" comment is a claim about *import order*, and import order in a
framework that bootstraps itself (as pytest-django does) is often not
what it looks like from inside your own file. Detecting *what's actually
running* (`'pytest' in sys.modules`, `sys.argv`, an explicitly-passed
setting) is more robust than racing a framework's own startup sequence.

```python
def test_creating_an_order_queues_email_after_items_exist(
    django_capture_on_commit_callbacks, api_client, admin_user, customer, product
):
    """The regression test for the $0.00-total bug: the confirmation
    email must reflect the order's ACTUAL total, not $0.00 from before
    OrderItems existed."""
    api_client.force_authenticate(user=admin_user)

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post("/api/orders/", {
            "customer": customer.pk,
            "status": "pending",
            "items": [{"product": product.pk, "quantity": 3, "unit_price": "10.00"}],
        }, format="json")

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert "$30.00" in mail.outbox[0].body  # NOT $0.00
```

`django_capture_on_commit_callbacks` is required here because
pytest-django wraps every test in a transaction that's rolled back at the
end — a transaction that never truly commits never fires its
`on_commit()` callbacks. This fixture captures them and runs them
explicitly, matching what happens for real once a transaction commits.

## 7. Scheduled tasks with Celery Beat

Not every background job is triggered by a user action — some just need
to run periodically:

```python
# catalog/tasks.py
@shared_task
def send_low_stock_report():
    from .models import Product

    low_stock = Product.objects.filter(is_active=True, quantity_in_stock__lte=F("reorder_level"))
    if not low_stock.exists():
        return "No low-stock products — nothing to report."

    lines = [f"- {p.name} ({p.sku}): {p.quantity_in_stock} left, reorder at {p.reorder_level}" for p in low_stock]
    send_mail(
        subject=f"Atlas: {low_stock.count()} product(s) need reordering",
        message="\n".join(lines),
        from_email=None,
        recipient_list=["manager@atlas.example"],
    )
    return f"Reported {low_stock.count()} low-stock product(s)."
```

```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'daily-low-stock-report': {
        'task': 'catalog.tasks.send_low_stock_report',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

Beat reads this schedule and enqueues `send_low_stock_report` every day
at 08:00 — nobody has to remember to check inventory manually.

## 8. Hands-on

In production (or to see this run for real, not just under tests), you
need Redis and two extra long-running processes alongside `runserver`:

```bash
# terminal 1 — Redis (via Docker; Module 16 formalizes this)
docker run -p 6379:6379 redis:7

# terminal 2 — the worker: picks up and executes queued tasks
celery -A config worker --loglevel=info    # add --pool=solo on Windows

# terminal 3 — beat: enqueues the scheduled low-stock report on time
celery -A config beat --loglevel=info

# terminal 4 — Django itself
python manage.py runserver
```

Place an order through `/api/orders/` and watch terminal 2 — you'll see
the task picked up and the "email" print to the console (our
`EMAIL_BACKEND` is still the console backend from development; Module 16
covers a real transactional email provider for production).

Run the test suite — no Redis, no worker, no beat process needed at all:

```bash
cd project/atlas
pytest -v orders/tests/test_tasks.py catalog/tests/test_tasks.py
```

### Exercise

Add a new scheduled task, `catalog/tasks.py::deactivate_stale_products`,
that marks any `Product` untouched (`updated_at` older than 180 days) as
`is_active=False`, wire it into `CELERY_BEAT_SCHEDULE` to run weekly, and
write a test proving it flips old products but leaves recently-updated
ones alone. As a design question (no code needed): should this send a
notification before deactivating, so nobody's surprised a product
vanished from the storefront?

## 9. Checkpoint — you should now be able to:

- [ ] Explain the four moving pieces (app, broker, worker, beat) and why
      a web process never runs task code itself.
- [ ] Write a `@shared_task` function that takes an ID and looks its
      object up fresh, and explain why.
- [ ] Queue a task from a `post_save` signal via `transaction.on_commit()`,
      and explain the exact bug it avoids.
- [ ] Explain why `CELERY_TASK_ALWAYS_EAGER` needs to be resolved
      carefully under pytest-django, and what `'pytest' in sys.modules`
      buys you that an env-var-in-conftest approach doesn't.
- [ ] Use `django_capture_on_commit_callbacks` to test `on_commit()` code.
- [ ] Schedule a periodic task with `CELERY_BEAT_SCHEDULE` + `crontab`.
- [ ] Have completed the stale-product exercise above.

## 10. What's next

**Module 14 — Real-World Features** builds the kind of everyday
functionality almost every production Django app needs: file/image
uploads (product photos), generated PDFs (order invoices), CSV export,
and better search/filtering — all things a real inventory system's users
would actually ask for.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 14.
