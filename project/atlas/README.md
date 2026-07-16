# Atlas

The portfolio project built throughout **Django Zero to Hero** — a store
inventory management + CRM platform. This app evolves module by module;
this README always reflects its *current* state (check git history for how
it got here).

## Current state (as of Module 03)

- Project `config/`, one app `pages/`.
- Three routes: home, products (hardcoded data), about — proving out
  URLs → views → templates → static files with template inheritance.
- **No database models yet** — that's Module 04. The products page currently
  reads from a hardcoded Python list in `pages/views.py` on purpose, so this
  module could focus entirely on the URL/view/template/static-file flow
  without the ORM's added complexity.

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

Then visit:
- http://127.0.0.1:8000/ — home
- http://127.0.0.1:8000/products/ — hardcoded product list
- http://127.0.0.1:8000/about/ — about page
- http://127.0.0.1:8000/admin/ — Django admin (no custom models registered yet)

## Structure

```
project/atlas/
├── manage.py
├── requirements.txt
├── config/              <- the Django PROJECT: settings + root URL config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── pages/                <- an APP: static-ish pages (home/products/about)
│   ├── views.py
│   └── urls.py           <- app-level URLconf, included from config/urls.py
├── templates/            <- project-wide templates
│   ├── base.html          <- shared layout, uses {% block %}
│   └── pages/              <- templates specific to the pages app
│       ├── home.html
│       ├── products.html
│       └── about.html
└── static/               <- project-wide static assets
    └── css/main.css
```
