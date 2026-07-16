# Atlas

The portfolio project built throughout **Django Zero to Hero** — a store
inventory management + CRM platform. This app evolves module by module;
this README always reflects its *current* state (check git history for how
it got here).

## Current state (as of Module 13)

- Project `config/`, apps: `accounts`, `pages`, `catalog`, `customers`, `orders`.
- Real data model, backed by migrations:
  - `catalog`: `Category`, `Supplier`, `Tag`, `Product` (FK to Category/Supplier, M2M to Tag)
  - `customers`: `Customer`
  - `orders`: `Order`, `OrderItem` (FK across all three apps)
  - `accounts`: custom `User` (extends `AbstractUser`) with a `role`
    (Customer/Sales Rep/Manager)
- Fully customized Django admin for every model (search, filters, inlines,
  bulk actions, autocomplete, branded as "Atlas Administration").
- `catalog` product CRUD on generic class-based views, with search and pagination.
- **Real authentication and authorization**: sign up / log in / log out,
  a "Sales Team" permission group seeded via data migration, and
  `catalog`'s create/update/delete views gated with
  `LoginRequiredMixin` + `PermissionRequiredMixin`. Anyone can browse
  products; only logged-in users with the right permission can manage them.
- **Bootstrap 5 frontend** (via CDN) with a small brand-specific
  `custom.css` layered on top, a real `/dashboard/` page (stat cards, low
  stock alert, recent orders) for logged-in users, and custom template
  tags/filters (`currency`, `low_stock_count`, `add_class`, `widget_type`).
- **A full JSON REST API** at `/api/` (Django REST Framework):
  categories/suppliers/tags/products/customers/orders, with the same
  permission rules as the web UI, token authentication (`/api/token/`), a
  writable nested `OrderSerializer` (create/update an order with its line
  items in one request), and a browsable API UI at `/api-auth/login/`.
- **A real automated test suite**: 45 tests (pytest-django + factory_boy),
  94% coverage — models, view permission gating, form/serializer
  validation, writable nested order API, query-count/caching proofs, and
  async task behavior. See `pytest.ini`, `conftest.py`, and each app's
  `factories.py`/`tests/`.
- **Query optimization & caching**: `Q`-based multi-field search,
  `select_related`/`prefetch_related` throughout, a race-condition-safe
  `Product.adjust_stock()` using `F()`, an `annotate`+`aggregate` average
  order value on the dashboard, a composite index matching the low-stock
  filter, and a cached (signal-invalidated) `low_stock_count`.
- **Background & scheduled tasks with Celery**: order confirmation emails
  send on a worker via `transaction.on_commit()` (not inline in the
  request), keeping order creation atomic so the email always reflects
  the order's real total; a daily low-stock report runs on a
  Celery Beat schedule. Tests run task code synchronously
  (`CELERY_TASK_ALWAYS_EAGER`) with no Redis/worker needed for the suite.

> ⚠️ If you cloned/ran this project before Module 08, delete your local
> `db.sqlite3` before migrating again — see the Module 08 lesson for why
> (switching `AUTH_USER_MODEL` after earlier migrations breaks a fresh `migrate`).

## Run it yourself

```bash
# from inside project/atlas/
python -m venv venv

# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt      # or requirements-dev.txt to include test tools
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run the test suite (no Redis or Celery worker needed — tasks run synchronously in tests):

```bash
pip install -r requirements-dev.txt
pytest -v
coverage run -m pytest && coverage report
```

To see background/scheduled tasks run for real, start Redis plus a worker
and beat alongside `runserver`:

```bash
docker run -p 6379:6379 redis:7
celery -A config worker --loglevel=info    # add --pool=solo on Windows
celery -A config beat --loglevel=info
```

Then visit:
- http://127.0.0.1:8000/ — home
- http://127.0.0.1:8000/accounts/signup/ — create an account (defaults to Customer role)
- http://127.0.0.1:8000/products/ — product list, search, create/edit/delete (permission-gated)
- http://127.0.0.1:8000/about/ — about page
- http://127.0.0.1:8000/admin/ — fully customized Django admin; add a user to the
  "Sales Team" group here to grant product management permissions
- http://127.0.0.1:8000/dashboard/ — stats dashboard (requires login)
- http://127.0.0.1:8000/api/ — browsable REST API (all models)
- http://127.0.0.1:8000/api/token/ — POST credentials to get an auth token

## Structure

```
project/atlas/
├── manage.py
├── requirements.txt
├── requirements-dev.txt  <- + pytest, pytest-django, factory-boy, coverage
├── pytest.ini
├── .coveragerc
├── conftest.py            <- shared pytest fixtures (category, product, sales_rep_user, ...)
├── config/              <- the Django PROJECT: settings + root URL config
│   └── celery.py           <- the Celery app (config_from_object + autodiscover_tasks)
├── accounts/             <- custom User model, signup/login/logout, roles/groups
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── factories.py        <- UserFactory
│   ├── tests/
│   └── migrations/        <- includes the "Sales Team" group data migration
├── pages/                <- Home/About/Dashboard
│   └── templatetags/       <- form_extras.py (add_class, widget_type)
├── catalog/              <- Category, Supplier, Tag, Product + permission-gated CRUD
│   ├── templatetags/       <- catalog_extras.py (currency, low_stock_count)
│   ├── serializers.py       <- DRF serializers
│   ├── api_views.py         <- DRF ViewSets
│   ├── cache.py              <- get_low_stock_count() (cached)
│   ├── signals.py            <- invalidates the cache on Product save/delete
│   ├── tasks.py               <- send_low_stock_report() (Celery Beat schedule)
│   ├── factories.py
│   └── tests/                <- test_models.py, test_views.py, test_api.py, test_query_optimization.py, test_tasks.py
├── customers/            <- Customer (+ serializers.py, api_views.py, factories.py, tests/)
├── orders/               <- Order, OrderItem (+ serializers.py, api_views.py, factories.py, tests/)
│   ├── signals.py           <- queues the confirmation email on order creation
│   └── tasks.py              <- send_order_confirmation_email()
├── api/                  <- just a URLconf: DefaultRouter wiring every ViewSet + token auth
├── templates/            <- project-wide templates
│   ├── base.html           <- Bootstrap 5, auth-aware nav
│   ├── registration/       <- login.html (Django's conventional path)
│   ├── accounts/           <- signup.html
│   ├── pages/               <- includes dashboard.html
│   └── catalog/
└── static/               <- project-wide static assets
    └── css/custom.css       <- brand overrides on top of Bootstrap
```
