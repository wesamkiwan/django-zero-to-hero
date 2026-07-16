# Module 03 — Django Fundamentals: Projects, Apps, URLs, Views, Templates

> **Where we're going:** the real **Atlas** project starts here. By the end,
> you'll understand exactly what `startproject`/`startapp` generate, how a
> request finds its way to a view, how views return HTML via templates, and
> how static files (CSS) get served — all four pieces most Django features
> touch.

## 1. Project vs. App — the distinction that confuses everyone at first

- A **project** is the whole website: global settings, the root URL config,
  and one or more apps wired together. You have exactly one project.
- An **app** is a self-contained feature area — in theory reusable across
  projects (e.g. a generic "blog" app), in practice usually specific to your
  project but still kept focused on one responsibility.

Atlas's project is called `config` (a project can be named anything —
`config` is a common professional convention, since the folder isn't really
"the app," it's project-wide configuration). Its first app is `pages`.

```bash
django-admin startproject config .    # the trailing "." = create files here,
                                       # not inside an extra config/ wrapper folder
python manage.py startapp pages
```

## 2. What `startproject` actually generated

```
manage.py            # CLI entry point — every command below runs through this
config/
  __init__.py
  settings.py         # ALL project configuration lives here
  urls.py             # the ROOT URL configuration — the first stop for every request
  wsgi.py             # entry point for traditional (sync) production servers
  asgi.py             # entry point for async-capable production servers
```

`manage.py` is just a thin wrapper: every command
(`runserver`, `migrate`, `startapp`, `test`, `shell`, ...) is really
`django-admin <command>` with `config.settings` pre-loaded as the settings
module. You'll type `python manage.py <something>` constantly from here on.

## 3. What `startapp` generated, and what we added

```
pages/
  __init__.py
  admin.py             # register models here for the admin site (Module 05)
  apps.py              # app configuration (rarely touched)
  migrations/          # database migration files (Module 04 — no models yet, so empty)
  models.py            # data definitions (Module 04)
  tests.py             # this app's tests (Module 11)
  views.py             # ← we wrote real views here
  urls.py              # ← we added this ourselves; startapp does NOT create it
```

`urls.py` isn't auto-generated per app — you create it yourself and
`include()` it from the project's root `config/urls.py`. This is the
standard pattern: **each app owns its own URL patterns**, and the project
just plugs them all together.

An app only "exists" to Django once it's added to `INSTALLED_APPS` in
`settings.py` — see `config/settings.py` in `project/atlas/`. Until then, its
templates, models, and management commands are invisible to the framework.

## 4. URLs — how a request finds a view

Every request is matched, top to bottom, against `urlpatterns` in the **root**
URLconf (`config/urls.py`), which usually just delegates into each app:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),   # delegate everything else to pages/urls.py
]
```

```python
# pages/urls.py
from django.urls import path
from . import views

app_name = "pages"   # namespace — see below

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('about/', views.about, name='about'),
]
```

- `path(route, view, name=...)` — `route` is matched against the URL path
  (after the parts already consumed by `include()`), `view` is the function
  to call, `name` lets you refer to this URL elsewhere without hardcoding it.
- **Path converters** capture parts of the URL as arguments to your view,
  with automatic validation and type conversion:
  `<int:product_id>`, `<slug:category_slug>`, `<uuid:order_id>`,
  `<str:...>` (default), `<path:...>` (matches slashes too).
  Go run `demo/url_converters/` now — it proves each of these with real
  requests, including a converter correctly rejecting the wrong shape (404).
- **Namespacing** (`app_name = "pages"`): lets you write
  `{% url 'pages:home' %}` in templates or `reverse('pages:home')` in Python,
  instead of hardcoding `/`. If you ever change the URL path, every
  reference updates automatically. **Never hardcode URLs** — always use
  `{% url %}` / `reverse()`.

## 5. Views — Python functions that answer requests

The simplest possible view:

```python
def home(request):
    return HttpResponse("Hello")
```

A view **always** takes `request` first, and **always** returns some kind of
`HttpResponse` (or raises an exception Django turns into one, like `Http404`).
`request` carries everything about the incoming request: `request.method`
(`'GET'`/`'POST'`/...), `request.GET` (query string as a dict-like object),
`request.POST` (form data — Module 06), `request.user` (Module 08).

Real views almost always use `render()` instead of building `HttpResponse`
by hand:

```python
from django.shortcuts import render

def products(request):
    context = {"products": PRODUCTS}          # a dict: template variable names → values
    return render(request, "pages/products.html", context)
```

`render()` = look up the template, fill in `context`, wrap the result in an
`HttpResponse`, all in one call. This is what every view in
`project/atlas/pages/views.py` does.

## 6. Templates — the Django Template Language (DTL)

Two kinds of syntax:
- `{{ variable }}` — print a value.
- `{% tag %}` — logic: loops, conditionals, inheritance, includes.

**Template inheritance** is the single most valuable DTL feature — define
shared layout once, override only what differs per page:

```django
{# base.html #}
<html>
<body>
  {% block content %}{% endblock %}
</body>
</html>
```
```django
{# pages/home.html #}
{% extends "base.html" %}
{% block content %}
  <h1>Home</h1>
{% endblock %}
```

Look at `project/atlas/templates/base.html` and
`project/atlas/templates/pages/products.html` for a real, working example —
note how `products.html` only defines the `content` block; the header, nav,
and footer come from `base.html` automatically.

Common tags you'll use constantly:

```django
{% for product in products %}
    <p>{{ product.name }}</p>
{% empty %}
    <p>No products.</p>
{% endfor %}

{% if product.in_stock %}
    In stock
{% else %}
    Out of stock
{% endif %}

{% url 'pages:products' %}      {# resolves to the actual path, e.g. /products/ #}
{% load static %}
<link rel="stylesheet" href="{% static 'css/main.css' %}">
```

### Template lookup order

Django looks for a template in this order:
1. Every directory listed in `TEMPLATES[0]['DIRS']` in `settings.py` —
   Atlas points this at `BASE_DIR / 'templates'` (project-wide templates,
   like `base.html`).
2. Each installed app's own `<app>/templates/` folder, **if**
   `APP_DIRS: True` (the default) — this is why `pages/`'s templates live at
   `templates/pages/*.html` at the project root here (we chose to centralize
   them; Django would equally find them inside `pages/templates/pages/` if
   we'd put them there instead — both are valid, centralizing is a style
   choice some teams prefer for visibility).

## 7. Static files — CSS, JS, images

- `STATIC_URL = 'static/'` — the URL *prefix* browsers use to fetch static
  assets (e.g. `/static/css/main.css`).
- `STATICFILES_DIRS` — where Django's dev server looks for those files
  *during development* (Atlas: `BASE_DIR / 'static'`).
- `{% load static %}` + `{% static 'css/main.css' %}` — always reference
  static files this way, never as a hardcoded `/static/...` string, for the
  same reason as `{% url %}`: one indirection point if things move.

This dev-server behavior (serving static files directly) is convenient but
**not how production works** — real deployments run `collectstatic` and let
Nginx/a CDN serve these files directly, which is far faster. That's covered
properly in Module 16; for now, just know `runserver`'s static file serving
is a development convenience, not production infrastructure.

## 8. Walk through Atlas yourself

Go to `project/atlas/`, read its `README.md`, and run it:

```bash
cd project/atlas
python -m venv venv
venv\Scripts\Activate.ps1        # or: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit all three pages (`/`, `/products/`, `/about/`) and open DevTools →
Elements to see the rendered HTML came from `base.html` + each page's block.
Then open `pages/views.py`, `pages/urls.py`, `templates/base.html`, and
`templates/pages/products.html` side by side and trace one full request:
URL → `urls.py` → `views.py` → `render()` → `products.html` → `base.html`.

### Exercise

Add a fourth page, `/contact/`:
1. Add a `contact` view in `pages/views.py` returning `render(request,
   "pages/contact.html", {})`.
2. Add its route to `pages/urls.py` with `name='contact'`.
3. Create `templates/pages/contact.html` extending `base.html` with a
   simple form (reuse the `.contact-form` styling already in `main.css`
   from the Module 02 mockup — same class names).
4. Add a nav link to it in `base.html` using `{% url 'pages:contact' %}`.

This exact loop — URL, view, template, (optionally) a nav link — is what
you'll repeat for every new page for the rest of the course.

## 9. Checkpoint — you should now be able to:

- [ ] Explain the difference between a Django *project* and an *app*.
- [ ] List what `startproject` and `startapp` each generate, and what each
      generated file is responsible for.
- [ ] Write a `path()` with at least two different converters and explain
      what each does.
- [ ] Explain why URLs should use `{% url %}`/`reverse()` instead of hardcoded strings.
- [ ] Write a function-based view using `render()` with a context dict.
- [ ] Build a template that extends a base layout and overrides one block.
- [ ] Explain what `STATIC_URL` vs `STATICFILES_DIRS` each do.
- [ ] Have completed the `/contact/` exercise above, running locally.

## 10. What's next

**Module 04 — Models & the ORM** replaces `pages/views.py`'s hardcoded
`PRODUCTS` list with real database-backed models — you'll define
`Product`, `Category`, `Customer`, `Supplier`, and see how little the
templates you just built have to change.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 04.
