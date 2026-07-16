# Atlas

The portfolio project built throughout **Django Zero to Hero** — a store
inventory management + CRM platform. This app evolves module by module;
this README always reflects its *current* state (check git history for how
it got here).

## Current state (as of Module 09)

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

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit:
- http://127.0.0.1:8000/ — home
- http://127.0.0.1:8000/accounts/signup/ — create an account (defaults to Customer role)
- http://127.0.0.1:8000/products/ — product list, search, create/edit/delete (permission-gated)
- http://127.0.0.1:8000/about/ — about page
- http://127.0.0.1:8000/admin/ — fully customized Django admin; add a user to the
  "Sales Team" group here to grant product management permissions
- http://127.0.0.1:8000/dashboard/ — stats dashboard (requires login)

## Structure

```
project/atlas/
├── manage.py
├── requirements.txt
├── config/              <- the Django PROJECT: settings + root URL config
├── accounts/             <- custom User model, signup/login/logout, roles/groups
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── migrations/        <- includes the "Sales Team" group data migration
├── pages/                <- Home/About/Dashboard
│   └── templatetags/       <- form_extras.py (add_class, widget_type)
├── catalog/              <- Category, Supplier, Tag, Product + permission-gated CRUD
│   └── templatetags/       <- catalog_extras.py (currency, low_stock_count)
├── customers/            <- Customer
├── orders/               <- Order, OrderItem
├── templates/            <- project-wide templates
│   ├── base.html           <- Bootstrap 5, auth-aware nav
│   ├── registration/       <- login.html (Django's conventional path)
│   ├── accounts/           <- signup.html
│   ├── pages/               <- includes dashboard.html
│   └── catalog/
└── static/               <- project-wide static assets
    └── css/custom.css       <- brand overrides on top of Bootstrap
```
