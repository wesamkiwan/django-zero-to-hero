# Atlas

The portfolio project built throughout **Django Zero to Hero** — a store
inventory management + CRM platform. This app evolves module by module;
this README always reflects its *current* state (check git history for how
it got here).

## Current state (as of Module 04)

- Project `config/`, apps: `pages`, `catalog`, `customers`, `orders`.
- Real data model, backed by migrations:
  - `catalog`: `Category`, `Supplier`, `Tag`, `Product` (FK to Category/Supplier, M2M to Tag)
  - `customers`: `Customer`
  - `orders`: `Order`, `OrderItem` (FK across all three apps)
- `/products/` now queries `Product.objects.filter(is_active=True)` for
  real — no more hardcoded data. The template needed no changes to support this.
- No admin customization, forms, or auth yet — that's Modules 05–08.

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
python manage.py runserver
```

The database starts empty. Populate it via `python manage.py shell` — see
`modules/04-models-orm/README.md` section 9 for a ready-to-paste script that
creates categories, a supplier, tagged products, a customer, and an order.

Then visit:
- http://127.0.0.1:8000/ — home
- http://127.0.0.1:8000/products/ — real products from the database
- http://127.0.0.1:8000/about/ — about page
- http://127.0.0.1:8000/admin/ — Django admin (no custom models registered yet — Module 05)

## Structure

```
project/atlas/
├── manage.py
├── requirements.txt
├── config/              <- the Django PROJECT: settings + root URL config
├── pages/                <- static-ish pages (home/products/about)
├── catalog/              <- Category, Supplier, Tag, Product
├── customers/            <- Customer
├── orders/               <- Order, OrderItem
├── templates/            <- project-wide templates
│   ├── base.html
│   └── pages/
└── static/               <- project-wide static assets
    └── css/main.css
```
