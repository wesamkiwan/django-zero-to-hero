# Atlas

The portfolio project built throughout **Django Zero to Hero** — a store
inventory management + CRM platform. This app evolves module by module;
this README always reflects its *current* state (check git history for how
it got here).

## Current state (as of Module 07)

- Project `config/`, apps: `pages`, `catalog`, `customers`, `orders`.
- Real data model, backed by migrations:
  - `catalog`: `Category`, `Supplier`, `Tag`, `Product` (FK to Category/Supplier, M2M to Tag)
  - `customers`: `Customer`
  - `orders`: `Order`, `OrderItem` (FK across all three apps)
- Fully customized Django admin for every model (search, filters, inlines,
  bulk actions, autocomplete, branded as "Atlas Administration").
- **`catalog` product CRUD is now built on Django's generic class-based
  views** (`ListView`/`DetailView`/`CreateView`/`UpdateView`/`DeleteView`)
  at `/products/`, with search, pagination, and validation — refactored
  from Module 06's hand-written function-based views with no template or
  URL changes.
- No authentication/roles yet — everyone can create/edit/delete products
  right now. That's Module 08.

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

The database starts empty — add products directly at `/products/create/`,
or via the admin (`createsuperuser` first).

Then visit:
- http://127.0.0.1:8000/ — home
- http://127.0.0.1:8000/products/ — product list, search, create/edit/delete
- http://127.0.0.1:8000/about/ — about page
- http://127.0.0.1:8000/admin/ — fully customized Django admin

## Structure

```
project/atlas/
├── manage.py
├── requirements.txt
├── config/              <- the Django PROJECT: settings + root URL config
├── pages/                <- Home/About
├── catalog/              <- Category, Supplier, Tag, Product + full product CRUD
│   ├── models.py
│   ├── forms.py           <- ProductForm (ModelForm + custom validation)
│   ├── views.py            <- ListView/DetailView/CreateView/UpdateView/DeleteView
│   └── urls.py
├── customers/            <- Customer
├── orders/               <- Order, OrderItem
├── templates/            <- project-wide templates
│   ├── base.html
│   ├── pages/
│   └── catalog/            <- product_list/detail/form/confirm_delete
└── static/               <- project-wide static assets
    └── css/main.css
```
