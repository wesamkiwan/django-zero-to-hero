# Overall Cheat Sheet — Django Zero to Hero

Every module's cheat sheet, concatenated in order. Each section here is a
copy of `modules/NN-slug/cheatsheet.md` — that per-module file is still
the canonical version if the two ever diverge; this document exists so
the whole course fits in one Ctrl-F.

## Table of contents

1. [Orientation, Environment, Python Refresher](#module-01--orientation-environment-python-refresher)
2. [Web & HTTP Fundamentals + HTML/CSS](#module-02--web--http-fundamentals--htmlcss)
3. [Django Fundamentals](#module-03--django-fundamentals)
4. [Models & the ORM](#module-04--models--the-orm)
5. [Django Admin Mastery](#module-05--django-admin-mastery)
6. [Forms & Function-Based Views (CRUD)](#module-06--forms--function-based-views-crud)
7. [Class-Based Views & Generic Views](#module-07--class-based-views--generic-views)
8. [Authentication, Authorization & Permissions](#module-08--authentication-authorization--permissions)
9. [Templates & Frontend Polish](#module-09--templates--frontend-polish)
10. [Django REST Framework](#module-10--django-rest-framework)
11. [Testing](#module-11--testing)
12. [Advanced ORM, Query Optimization & Caching](#module-12--advanced-orm-query-optimization--caching)
13. [Celery & Background/Async Tasks](#module-13--celery--backgroundasync-tasks)
14. [Real-World Features](#module-14--real-world-features)
15. [Security Best Practices](#module-15--security-best-practices)
16. [Configuration, Docker & Deployment](#module-16--configuration-docker--deployment)
17. [Git Workflow, System Design & Job Readiness](#module-17--git-workflow-system-design--job-readiness)

---

## Module 01 — Orientation, Environment, Python Refresher

### Core concepts

| Term | Meaning |
|---|---|
| Client | The browser/app that sends requests |
| Server | The program (Django) that responds to requests |
| Frontend | What the user sees (HTML/CSS/JS) |
| Backend | Server-side logic (Django's job) |
| MVT | Model (data) → View (logic) → Template (presentation) |
| Request/Response cycle | Browser asks → server answers, repeat |

### Virtual environments

```bash
python -m venv venv                     # create
venv\Scripts\Activate.ps1               # activate (Windows PowerShell)
source venv/bin/activate                # activate (macOS/Linux)
deactivate                              # exit the venv
```
Never commit `venv/`. Commit `requirements.txt` instead.

### pip

```bash
pip install <package>
pip install <package>==<version>        # pin exact version (recommended)
pip install -r requirements.txt         # install everything listed
pip freeze > requirements.txt           # capture current environment
pip list
pip uninstall <package>
```

### Git essentials

```bash
git status
git add <file>            # or: git add .
git commit -m "message"
git log --oneline
git push
git pull
```

### Django project anatomy (from the hello_django demo)

```
manage.py            # CLI entry point: runserver, migrate, startapp, test, ...
mysite/               # the PROJECT: global settings + root URL config
  settings.py
  urls.py
greetings/            # an APP: one self-contained feature area
  views.py            # functions/classes: request in, response out
  models.py           # data definitions (Module 04)
  admin.py            # admin registration (Module 05)
```

```bash
django-admin startproject <name> .      # create a project in the current dir
python manage.py startapp <name>        # create a new app
python manage.py runserver              # run the dev server (default: :8000)
```

### Python OOP quick reference (Django-relevant)

```python
# Class + constructor
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

# Inheritance + overriding + super()
class Base:
    def greet(self):
        return "hi"

class Child(Base):
    def greet(self):
        return super().greet() + " there"

# Class attribute + classmethod
class Counter:
    total = 0
    def __init__(self):
        Counter.total += 1
    @classmethod
    def how_many(cls):
        return cls.total

# *args / **kwargs — every Django view can receive these
def view(request, *args, **kwargs):
    ...

# Comprehensions
squares = [n * n for n in range(5)]
lookup = {n: n * n for n in range(5)}

# Context manager
with open("file.txt") as f:
    data = f.read()
```

### Mental model to keep forever

```
Request → urls.py (routing) → views.py (logic) → models.py (data)
                                    │
                                    ▼
                          templates/*.html (HTML out)
```

---

## Module 02 — Web & HTTP Fundamentals + HTML/CSS

### URL anatomy

```
https://host:port/path?query#fragment
```
Fragment never reaches the server. Query string → Django's `request.GET`.

### HTTP methods

| Method | Use | Changes data? |
|---|---|---|
| GET | fetch a resource | No — must be safe/idempotent |
| POST | create / submit | Yes |
| PUT | replace entirely | Yes |
| PATCH | partial update | Yes |
| DELETE | remove | Yes |
| HEAD | headers only, no body | No |
| OPTIONS | discover allowed methods | No |

### Status code categories

| First digit | Category | Fault |
|---|---|---|
| 2xx | Success | — |
| 3xx | Redirection | — |
| 4xx | Client error | You/the request |
| 5xx | Server error | The server |

Memorize: `200` OK · `201` Created · `301`/`302` redirect · `400` bad request ·
`401` unauthorized (not logged in) · `403` forbidden (logged in, not allowed) ·
`404` not found · `405` method not allowed · `500` server exception.

### Key headers

| Header | Direction | Meaning |
|---|---|---|
| `Host` | request | which site |
| `User-Agent` | request | client identity |
| `Content-Type` | both | body format |
| `Authorization` | request | credentials/token |
| `Cookie` | request | send stored cookies back |
| `Set-Cookie` | response | ask browser to store a cookie |
| `Location` | response | where to redirect to |

### Cookies/sessions in one sentence

Server sets a `sessionid` cookie → browser auto-sends it on every future
request → server looks up session data by that ID. This is how "being
logged in" survives across stateless requests.

### HTML skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>...</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>...</header>
    <nav>...</nav>
    <main>
        <h1>...</h1>
        <form method="post" action="...">
            <input type="text" name="...">
            <button type="submit">Send</button>
        </form>
    </main>
    <footer>...</footer>
</body>
</html>
```

### CSS essentials

```css
* { box-sizing: border-box; }         /* padding/border inside declared width */

.class-selector { }
#id-selector    { }
tag-selector    { }

/* Flexbox — one dimension */
.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Grid — two dimensions, responsive without media queries */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}
```

### DevTools

`F12` → **Network** tab = inspect real requests/responses.
`F12` → **Elements** tab = inspect/live-edit HTML & CSS.

---

## Module 03 — Django Fundamentals

### Commands

```bash
django-admin startproject config .     # new project in the current dir
python manage.py startapp pages        # new app
python manage.py runserver             # dev server, default :8000
python manage.py runserver 8080        # dev server on a specific port
python manage.py migrate               # apply migrations (needed even with no custom models)
python manage.py shell                 # Python shell with Django loaded
```

### Project vs App

| | Project | App |
|---|---|---|
| Count | exactly one | one or more |
| Contains | settings, root urls | views, models, templates for one feature area |
| Example | `config/` | `pages/` |
| Must be registered? | — | yes, in `INSTALLED_APPS` |

### URLs

```python
# root urls.py
from django.urls import include, path
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
]

# app urls.py
app_name = "pages"                      # enables namespacing
urlpatterns = [
    path('', views.home, name='home'),
    path('products/<int:pk>/', views.detail, name='detail'),
]
```

Reference by name, never hardcode:
```django
{% url 'pages:home' %}
```
```python
from django.urls import reverse
reverse('pages:home')
```

### Path converters

| Converter | Matches | View receives |
|---|---|---|
| `str` (default) | anything except `/` | `str` |
| `int` | digits only | `int` |
| `slug` | letters/numbers/hyphens/underscores | `str` |
| `uuid` | a valid UUID | `UUID` |
| `path` | anything, including `/` | `str` |

### Views

```python
from django.shortcuts import render
from django.http import HttpResponse, Http404

def my_view(request):
    return HttpResponse("plain text/html")

def my_view2(request):
    context = {"key": "value"}
    return render(request, "app/template.html", context)
```
`request.method`, `request.GET`, `request.POST`, `request.user` (Module 08).

### Templates (DTL)

```django
{{ variable }}
{{ variable|default:"fallback" }}

{% extends "base.html" %}
{% block content %}...{% endblock %}

{% for item in items %}...{% empty %}no items{% endfor %}
{% if condition %}...{% elif other %}...{% else %}...{% endif %}

{% url 'app:name' arg1 %}

{% load static %}
{% static 'css/main.css' %}
```

Template lookup order: `TEMPLATES[0]['DIRS']` first, then each app's own
`templates/` folder (if `APP_DIRS: True`).

### Static files

```python
# settings.py
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']   # dev-time lookup locations
```
```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/main.css' %}">
```
Production uses `collectstatic` + a real web server/CDN (Module 16) — dev
server static serving is convenience only.

### Request → response, the whole path

```
URL hits config/urls.py
  → include('pages.urls') delegates to pages/urls.py
    → path() matches, calls a view in pages/views.py
      → view calls render(request, template, context)
        → template extends base.html, fills in {% block %}
          → HttpResponse sent back to the browser
```

---

## Module 04 — Models & the ORM

### Migration commands

```bash
python manage.py makemigrations [app_label]   # generate migration file(s)
python manage.py migrate                      # apply them
python manage.py sqlmigrate app_label 0001    # see the actual SQL a migration runs
python manage.py showmigrations               # see applied/unapplied migrations
```

### Common field types

```python
models.CharField(max_length=100)
models.TextField()
models.SlugField()
models.EmailField()
models.IntegerField() / models.PositiveIntegerField()
models.DecimalField(max_digits=10, decimal_places=2)   # use for money, never FloatField
models.BooleanField(default=True)
models.DateTimeField(auto_now_add=True)   # set once, at creation
models.DateTimeField(auto_now=True)       # updated on every save
```

Common options: `null=True` (DB-level), `blank=True` (form-level),
`default=`, `unique=True`, `choices=`.

### Choices (modern pattern)

```python
class Status(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"

status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
# order.get_status_display() -> human-readable label
```

### Relationships

```python
# Many-to-one
category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

# Many-to-many
tags = models.ManyToManyField(Tag, blank=True, related_name="products")

# One-to-one
profile = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="profile")
```

`on_delete` choices: `CASCADE` (delete children too), `PROTECT` (block
deletion while children exist), `SET_NULL` (needs `null=True`),
`SET_DEFAULT`, `DO_NOTHING` (rarely safe).

Traversal:
```python
category.products.all()   # reverse FK, via related_name
product.tags.all()        # forward M2M
tag.products.all()        # reverse M2M, via related_name
author.profile            # forward O2O
profile.author            # reverse O2O
```

### QuerySets

```python
Model.objects.all()
Model.objects.filter(field=value)
Model.objects.exclude(field=value)
Model.objects.get(field=value)              # exactly one, or raises
Model.objects.order_by("field", "-other")   # "-" = descending
Model.objects.values("field1", "field2")    # dicts, not instances
Model.objects.get_or_create(field=value, defaults={...})
```

Field lookups: `__gt` `__gte` `__lt` `__lte` `__contains` `__icontains`
`__in` `__isnull` — and traverse relations with `__`: `product__category__name`.

QuerySets are **lazy** — building one issues no query; iterating,
`list()`-ing, or printing it does.

### Model methods worth always writing

```python
def __str__(self):
    return self.name          # readable everywhere: admin, shell, errors

def get_absolute_url(self):
    return reverse("app:detail", args=[self.pk])

@property
def computed_thing(self):
    return self.a + self.b    # accessed WITHOUT parens: obj.computed_thing
```

### Meta options

```python
class Meta:
    ordering = ["name"]
    verbose_name_plural = "categories"
    indexes = [models.Index(fields=["sku"])]
    constraints = [models.UniqueConstraint(fields=["order", "product"], name="...")]
```

### Shell

```bash
python manage.py shell
```

---

## Module 05 — Django Admin Mastery

### Minimum registration

```python
from django.contrib import admin
from .models import Supplier
admin.site.register(Supplier)
```

### Customized registration

```python
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "product_count"]
    list_filter = ["some_field"]
    search_fields = ["name"]
    list_editable = ["some_editable_field"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["related_fk_field"]   # target admin needs search_fields
    filter_horizontal = ["m2m_field"]            # nicer widget for M2M

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()

    @admin.display(description="Reorder?", boolean=True)
    def reorder_flag(self, obj):
        return obj.needs_reorder()
```

`list_display` can reference: model fields, model `@property`/methods, or
methods defined on the `ModelAdmin` itself.

### Inlines

```python
class OrderItemInline(admin.TabularInline):   # or StackedInline
    model = OrderItem
    extra = 1
    autocomplete_fields = ["product"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
```

`TabularInline` = compact table. `StackedInline` = one full form block per
related object — use for models with many fields.

### Actions

```python
@admin.action(description="Mark selected as inactive")
def mark_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} updated.")

class ProductAdmin(admin.ModelAdmin):
    actions = [mark_inactive]
```

`queryset.update(...)` = one SQL `UPDATE` for all selected rows — don't
loop and `.save()` each instance individually.

### Branding

```python
# urls.py, before urlpatterns
admin.site.site_header = "Atlas Administration"
admin.site.site_title = "Atlas Admin"
admin.site.index_title = "Store & CRM Management"
```

### Commands

```bash
python manage.py createsuperuser
```

### Testing admin programmatically (no browser needed)

```python
from django.test import Client
c = Client()
c.login(username="admin", password="...")
resp = c.get("/admin/catalog/product/")
resp = c.post("/admin/catalog/product/", {
    "action": "mark_inactive",
    "_selected_action": ["1", "2"],
    "index": "0",
    "select_across": "0",
})
```

---

## Module 06 — Forms & Function-Based Views (CRUD)

### ModelForm

```python
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", ...]      # always explicit, never "__all__"
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_price(self):                    # single-field validation
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("...")
        return price

    def clean(self):                          # cross-field validation
        cleaned_data = super().clean()
        ...
        return cleaned_data
```

### CSRF

```django
<form method="post">
    {% csrf_token %}
    ...
</form>
```
Missing it on a POST form → Django rejects with 403. Always include it.

### The five-view CRUD pattern

```python
def x_list(request):
    qs = Model.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    return render(request, "app/x_list.html", {"objects": qs, "query": q})

def x_detail(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    return render(request, "app/x_detail.html", {"object": obj})

def x_create(request):
    if request.method == "POST":
        form = XForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Created.")
            return redirect("app:x_detail", pk=obj.pk)
    else:
        form = XForm()
    return render(request, "app/x_form.html", {"form": form})

def x_update(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    if request.method == "POST":
        form = XForm(request.POST, instance=obj)   # <- instance= makes it an UPDATE
        if form.is_valid():
            form.save()
            messages.success(request, "Updated.")
            return redirect("app:x_detail", pk=obj.pk)
    else:
        form = XForm(instance=obj)
    return render(request, "app/x_form.html", {"form": form})

def x_delete(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Deleted.")
        return redirect("app:x_list")
    return render(request, "app/x_confirm_delete.html", {"object": obj})
```

### Post/Redirect/Get (PRG)

After a successful POST → always `redirect()` to a GET URL. Never
`render()` directly after a successful POST — that's what causes
"resubmit form?" browser warnings on refresh.

### Messages

```python
from django.contrib import messages
messages.success(request, "...")
messages.error(request, "...")
messages.warning(request, "...")
messages.info(request, "...")
```
```django
{% if messages %}
    {% for message in messages %}
        <p class="message-{{ message.tags }}">{{ message }}</p>
    {% endfor %}
{% endif %}
```

### Template form rendering

```django
<form method="post" class="model-form">
    {% csrf_token %}
    {{ form.non_field_errors }}
    {{ form.as_p }}          {# or render fields manually for full control #}
    <button type="submit">Save</button>
</form>
```

### Search via request.GET

```python
query = request.GET.get("q", "").strip()
if query:
    qs = qs.filter(name__icontains=query)
```

---

## Module 07 — Class-Based Views & Generic Views

### URL wiring

```python
path('', views.ProductListView.as_view(), name='product_list'),
```

### The five generic views

```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

class ProductListView(ListView):
    model = Product
    context_object_name = "products"     # default: "product_list"/"object_list"
    paginate_by = 12                      # free pagination

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        return qs.filter(name__icontains=q) if q else qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)   # ALWAYS call super() first
        context["extra"] = "..."
        return context


class ProductDetailView(DetailView):
    model = Product
    # default context names: "object" AND "<model_name_lowercase>"


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    # success_url not needed if model.get_absolute_url() exists

    def form_valid(self, form):
        response = super().form_valid(form)   # does form.save() + builds redirect
        messages.success(self.request, "Created.")
        return response


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    # same form_valid() pattern as CreateView


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("catalog:product_list")   # required — no natural default

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "Deleted.")
        return HttpResponseRedirect(success_url)
```

### Default template names (convention over configuration)

| View | Default template |
|---|---|
| `ListView` | `<app>/<model>_list.html` |
| `DetailView` | `<app>/<model>_detail.html` |
| `CreateView` / `UpdateView` | `<app>/<model>_form.html` |
| `DeleteView` | `<app>/<model>_confirm_delete.html` |

### Default context variable names

| View | Provides |
|---|---|
| `ListView` | `object_list` (or `<model>_list`), override via `context_object_name` |
| `DetailView` / `UpdateView` | `object` and `<model_name>` |
| `CreateView` | `form` (no object until saved) |

### `reverse` vs `reverse_lazy`

- **Class body / class attribute** (evaluated at import time): use `reverse_lazy`.
- **Inside a method** (evaluated per-request, URLconf already loaded): `reverse` is fine.

### Pagination template snippet

```django
{% if is_paginated %}
    {% if page_obj.has_previous %}<a href="?page={{ page_obj.previous_page_number }}">Prev</a>{% endif %}
    Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
    {% if page_obj.has_next %}<a href="?page={{ page_obj.next_page_number }}">Next</a>{% endif %}
{% endif %}
```

### Decision rule

Use a generic CBV for standard "fetch object(s) / render or process a form"
CRUD. Use a plain function view when the logic doesn't map onto that shape
(webhooks, multi-purpose branching views, one-off redirects).

---

## Module 08 — Authentication, Authorization & Permissions

### Custom User model (set up BEFORE the first migrate!)

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        SALES_REP = "sales_rep", "Sales Rep"
        MANAGER = "manager", "Manager"
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
```
```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

**Gotcha**: changing `AUTH_USER_MODEL` after other apps' migrations (esp.
`admin`) have applied against the old model → `InconsistentMigrationHistory`.
Fresh database only, or a real (painful) data migration in production.

### Login / logout / signup

```python
# urls.py
from django.contrib.auth import views as auth_views
path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
path("logout/", auth_views.LogoutView.as_view(), name="logout"),   # POST only, Django 4.1+
path("signup/", views.SignUpView.as_view(), name="signup"),
```
```python
# forms.py
from django.contrib.auth.forms import UserCreationForm
class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")   # never include "role" or similar
```
```python
# views.py
from django.contrib.auth import login
class SignUpView(CreateView):
    form_class = SignUpForm
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
```
```django
<!-- logout must be a POST form, not a link -->
<form method="post" action="{% url 'accounts:logout' %}">
    {% csrf_token %}
    <button type="submit">Log out</button>
</form>
```

### Settings

```python
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'pages:home'
LOGOUT_REDIRECT_URL = 'pages:home'
```

### Permissions & groups

Every model auto-gets 4 permissions: `add_<model>`, `change_<model>`,
`delete_<model>`, `view_<model>`.

```python
# Gate a CBV
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_product"
```
Order: `LoginRequiredMixin` before `PermissionRequiredMixin`, both before the view class.

```django
{% if perms.catalog.add_product %}...{% endif %}   {# UI hint only — not real security #}
```

### Seeding a group via data migration

```python
def create_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct, _ = ContentType.objects.get_or_create(app_label="catalog", model="product")
    perms = [
        Permission.objects.get_or_create(
            content_type=ct, codename=f"{a}_product", defaults={"name": f"Can {a} product"}
        )[0] for a in ("add", "change", "delete")
    ]
    group, _ = Group.objects.get_or_create(name="Sales Team")
    group.permissions.set(perms)
```
Use `get_or_create`, never `get()` — permissions may not exist yet when a
data migration runs mid-`migrate` (they're created by a `post_migrate`
signal at the very end of the run).

### Checking permissions in Python

```python
user.has_perm("catalog.add_product")
user.groups.add(some_group)
user.is_superuser        # bypasses ALL permission checks
```

---

## Module 09 — Templates & Frontend Polish

### Bootstrap via CDN

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```
Fine for learning/dev; Module 16 covers bundling your own static assets for production.

### Custom template filter

```python
# <app>/templatetags/__init__.py must exist (empty file)
# <app>/templatetags/my_extras.py
from django import template
register = template.Library()

@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def currency(value):
    return f"${value:,.2f}"
```
```django
{% load my_extras %}
{{ form.name|add_class:"form-control" }}
{{ product.price|currency }}
```

### Custom simple_tag

```python
@register.simple_tag
def low_stock_count():
    return Product.objects.filter(quantity_in_stock__lte=F("reorder_level")).count()
```
```django
{% load catalog_extras %}
{% low_stock_count %}
```
Runs a fresh query every call — don't put an expensive one in the nav
without caching (Module 12).

### Django templates forbid underscore attribute access

`{{ obj.__class__ }}` never works — silently resolves to nothing. Need a
Python-side attribute lookup? Write a filter:
```python
@register.filter
def widget_type(field):
    return field.field.widget.__class__.__name__
```

### F() expressions — compare two fields in the database

```python
from django.db.models import F
Product.objects.filter(quantity_in_stock__lte=F("reorder_level"))
```

### select_related — avoid N+1 queries across a FK

```python
Order.objects.select_related("customer").order_by("-created_at")[:5]
```
Without it: 1 query for orders + 1 extra query per order to fetch
`.customer`. With it: 1 query total (SQL JOIN). Deep dive in Module 12.

### login_required (function-based view equivalent of LoginRequiredMixin)

```python
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    ...
```

### Layout that applies to every page → base.html, not every child

```django
<!-- base.html -->
<div class="container">
    {% block content %}{% endblock %}
</div>
```
Child templates write content directly — no repeated `<div class="container">`.

### Returning HTML from a filter (needs mark_safe — see Module 15 for why)

```python
from django.utils.safestring import mark_safe

@register.filter
def stock_badge(product):
    if product.in_stock:
        return mark_safe('<span class="badge bg-success">In stock</span>')
    return mark_safe('<span class="badge bg-danger">Out of stock</span>')
```

---

## Module 10 — Django REST Framework

### Install & register

```bash
pip install djangorestframework
```
```python
INSTALLED_APPS += ["rest_framework", "rest_framework.authtoken"]
```

### Serializer

```python
class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)  # nested read
    computed = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [...]
        read_only_fields = ["created_at", "updated_at"]

    def get_computed(self, obj):
        return obj.some_method()

    def validate_price(self, value):        # single-field, mirrors ModelForm.clean_<field>
        if value <= 0:
            raise serializers.ValidationError("...")
        return value

    def validate(self, data):                # cross-field, mirrors ModelForm.clean()
        ...
        return data
```

### Writable nested serializer (NOT automatic — override create/update)

```python
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        # ... update instance fields ...
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        return instance
```

### ViewSet + router

```python
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    def get_queryset(self):
        return Product.objects.select_related("category").prefetch_related("tags")
```
```python
# api/urls.py
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
urlpatterns = [path("", include(router.urls))]
```
Generates: `GET/POST /products/`, `GET/PUT/PATCH/DELETE /products/<pk>/`.

### Custom action on a ViewSet

```python
from rest_framework.decorators import action
from rest_framework.response import Response

@action(detail=False, methods=["get"])
def low_stock(self, request):
    qs = self.get_queryset().filter(quantity_in_stock__lte=F("reorder_level"))
    return Response(self.get_serializer(qs, many=True).data)
```

### Settings

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
```
`DjangoModelPermissionsOrAnonReadOnly` reuses the SAME Django permissions
(`app.add_model` etc.) the admin/web views already enforce.

### Token auth

```
POST /api/token/  {"username": "...", "password": "..."}  ->  {"token": "..."}
```
```bash
curl -H "Authorization: Token <token>" http://.../api/products/
```

### Browsable API & login

```python
path('api-auth/', include('rest_framework.urls')),
```
Visit any API endpoint in a browser for an interactive HTML view with forms.

### Testing the API (DRF's test client)

```python
from rest_framework.test import APIClient
c = APIClient()
c.credentials(HTTP_AUTHORIZATION=f"Token {token}")
resp = c.post("/api/products/", {...}, format="json")
resp.json()
```

### Pagination response shape

```json
{"count": 42, "next": "...?page=2", "previous": null, "results": [...]}
```

---

## Module 11 — Testing

### Setup

```bash
pip install pytest pytest-django factory-boy coverage
```
```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
addopts = --reuse-db
```
```ini
# .coveragerc
[run]
omit = */migrations/*, manage.py, */tests/*, conftest.py, */factories.py
```

### Factory

```python
class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")   # unique per call
    category = factory.SubFactory(CategoryFactory)        # auto-creates related obj
    price = Decimal("19.99")                              # Decimal, NOT a plain string!
```

**Gotcha**: Django only coerces a `DecimalField` input to `Decimal` when it
passes through a Form/Serializer's validation. A factory (or any direct
`Model.objects.create(...)`) that hands it a raw string leaves it a `str`
in memory — arithmetic on it either errors (`str - str`) or silently gives
the wrong answer (`"10.00" * 3 == "10.0010.0010.00"`, string repetition).
Always pass `Decimal(...)` in factories/tests for decimal fields.

### Custom post_generation hook (future-proof over PostGenerationMethodCall)

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")
        if create:
            self.save()
```

### conftest.py fixtures

```python
@pytest.fixture
def product(category, supplier):
    return ProductFactory(category=category, supplier=supplier)

@pytest.fixture
def sales_rep_user(sales_team_group):
    user = UserFactory()
    user.groups.add(sales_team_group)
    return user

@pytest.fixture
def api_client():
    return APIClient()
```
Any test function that names a fixture as a parameter gets it injected
automatically — no imports needed.

### Writing tests

```python
pytestmark = pytest.mark.django_db   # module-level: every test gets DB access

def test_something(client, product):             # Django test client
    response = client.get(reverse("catalog:product_list"))
    assert response.status_code == 200

def test_permission(client, customer_user):
    client.force_login(customer_user)             # skip the actual login form
    response = client.get(reverse("catalog:product_create"))
    assert response.status_code == 403

def test_api(api_client, sales_rep_user):          # DRF's APIClient
    api_client.force_authenticate(user=sales_rep_user)
    response = api_client.post("/api/products/", {...}, format="json")
    assert response.status_code == 201
```

### Running

```bash
pytest                    # everything
pytest catalog/           # one app
pytest -k "permission"    # name matches
pytest -v                 # verbose

coverage run -m pytest
coverage report
coverage html              # htmlcov/index.html
```

### TDD in one sentence

For a new rule (validation, permission boundary): write the failing test
first — it forces you to state "correct" precisely before you're biased
by the implementation you're about to write.

---

## Module 12 — Advanced ORM, Query Optimization & Caching

### select_related vs prefetch_related

```python
Order.objects.select_related("customer")             # FK/O2O — one query, SQL JOIN
Product.objects.prefetch_related("tags")              # M2M/reverse FK — 2 queries, stitched in Python
Product.objects.select_related("category").prefetch_related("tags")   # combine freely
```

### Proving query counts in tests

```python
def test_x(django_assert_num_queries):
    with django_assert_num_queries(1):
        list(Order.objects.select_related("customer"))
```

### Q objects — OR

```python
from django.db.models import Q
qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q))
```
Plain `filter(a=1, b=2)` always ANDs. Use `Q` for OR.

### F() — compare AND atomically update

```python
from django.db.models import F

# Compare two fields on the same row
Product.objects.filter(quantity_in_stock__lte=F("reorder_level"))

# Atomic update — avoids the race condition of read-modify-write
Product.objects.filter(pk=pk).update(quantity_in_stock=F("quantity_in_stock") - 1)
```
NEVER: `obj.quantity_in_stock -= 1; obj.save()` under concurrency — two
requests reading the same stale value both write, one update is silently lost.

### annotate() vs aggregate()

```python
Category.objects.annotate(product_count=Count("products"))   # per-row value
Product.objects.aggregate(Avg("price"))                        # one summary value

# Can't aggregate a Python @property — annotate first, then aggregate the annotation:
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce

orders = Order.objects.annotate(
    computed_total=Coalesce(Sum(F("items__quantity") * F("items__unit_price")),
                             Decimal("0.00"), output_field=DecimalField())
)
orders.aggregate(avg=Avg("computed_total"))
```

### Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=["sku"]),
        models.Index(fields=["is_active", "quantity_in_stock"]),   # composite, matches real filter
    ]
```
Match your actual frequent filter columns — don't index speculatively.

### Caching

```python
# settings.py
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
```
```python
from django.core.cache import cache

cache.get_or_set(key, lambda: expensive_query(), timeout_seconds)
cache.delete(key)
```

### Signal-based cache invalidation

```python
# app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_cache(sender, **kwargs):
    cache.delete(CACHE_KEY)
```
```python
# app/apps.py
class MyAppConfig(AppConfig):
    def ready(self):
        from . import signals  # registers the @receiver hooks
```

### Admin N+1 fix

```python
def get_queryset(self, request):
    return super().get_queryset(request).annotate(product_count=Count("products"))

@admin.display(description="Products", ordering="product_count")
def product_count(self, obj):
    return obj.product_count   # from the annotation, not obj.products.count()
```

---

## Module 13 — Celery & Background/Async Tasks

### The four pieces

- **App** (`config/celery.py`) — knows about your tasks & broker.
- **Broker** (Redis) — the queue; `.delay()` drops a message on it and returns instantly.
- **Worker** (`celery -A config worker`) — separate process, actually runs task code.
- **Beat** (`celery -A config beat`) — separate process, enqueues scheduled tasks on time.

Your Django/web process **never executes task code** — it only enqueues.

### Wiring

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

### Writing a task

```python
from celery import shared_task

@shared_task
def send_order_confirmation_email(order_id):   # ID, not an instance — must be JSON-serializable
    from .models import Order                     # local import — models may not be ready yet
    order = Order.objects.select_related("customer").get(pk=order_id)
    ...
```

### Queuing from a signal, safely

```python
@receiver(post_save, sender=Order)
def queue_order_confirmation_email(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(lambda: send_order_confirmation_email.delay(instance.pk))
```
Wrap the multi-step creation that fires the signal in `transaction.atomic()`
too — otherwise `on_commit()` still has nothing complete to wait for.

### Testing — CELERY_TASK_ALWAYS_EAGER

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

### Scheduling with Beat

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'daily-low-stock-report': {
        'task': 'catalog.tasks.send_low_stock_report',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

### Running it for real

```bash
docker run -p 6379:6379 redis:7
celery -A config worker --loglevel=info    # --pool=solo on Windows
celery -A config beat --loglevel=info
python manage.py runserver
```

---

## Module 14 — Real-World Features

### File/image uploads

```python
image = models.ImageField(upload_to="products/", blank=True, null=True)   # requires Pillow
```
```python
# settings.py
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```
```python
# urls.py — dev only, never in production
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
```html
<form method="post" enctype="multipart/form-data">   <!-- easy to forget, silently drops the file -->
```
Testing uploads:
```python
# conftest.py
@pytest.fixture(autouse=True)
def _tmp_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path   # keeps test uploads out of the real media/ dir

TINY_GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
SimpleUploadedFile("x.gif", TINY_GIF, content_type="image/gif")
```

### PDF generation (reportlab)

```python
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

buffer = io.BytesIO()
pdf = canvas.Canvas(buffer, pagesize=letter)
pdf.drawString(x, y, "text")
pdf.showPage(); pdf.save()

response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
response["Content-Disposition"] = 'attachment; filename="x.pdf"'
```
Test it's real: `assert response.content.startswith(b"%PDF")`.

### CSV export (standard library, no dependency)

```python
import csv
response = HttpResponse(content_type="text/csv")
response["Content-Disposition"] = 'attachment; filename="x.csv"'
writer = csv.writer(response)   # HttpResponse is file-like enough for csv.writer
writer.writerow([...])
```
Admin bulk action version:
```python
@admin.action(description="Export selected as CSV")
def export_as_csv(modeladmin, request, queryset):
    ...
    return response

class XAdmin(admin.ModelAdmin):
    actions = [export_as_csv]
```
Share filtering logic between the list view and the export instead of
duplicating it — one function both call.

### Filtering (extends Module 12's Q search)

```python
qs.filter(category_id=category_id)
qs.filter(quantity_in_stock__lte=F("reorder_level"))   # "low" stock
qs.filter(quantity_in_stock=0)                          # "out" of stock
```
Preserve every active filter across pagination links, not just the search term.

### Permission gaps surfaced by a new feature

A new view needing `app.view_model` doesn't mean that permission exists
on any group yet — check, and add a data migration if not (same pattern
as `accounts/migrations/0002_create_sales_team_group.py`):
```python
group.permissions.add(Permission.objects.get_or_create(
    content_type=ContentType.objects.get_or_create(app_label="orders", model="order")[0],
    codename="view_order", defaults={"name": "Can view order"},
)[0])
```

### Notifications app

```python
# models.py
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at", "-pk"]   # -pk tiebreaker for same-instant timestamps
```
```python
# a second @receiver on a signal Module 13 already uses — both run
@receiver(post_save, sender=Order)
def notify_managers_of_new_order(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.bulk_create([...])   # plain DB write, no on_commit/Celery needed here
```

### Context processors

```python
# app/context_processors.py
def unread_count(request):
    if not request.user.is_authenticated:
        return {}
    return {"unread_notification_count": ...}
```
```python
# settings.py
TEMPLATES = [{"OPTIONS": {"context_processors": [..., "notifications.context_processors.unread_count"]}}]
```
Now available in **every** template automatically — same mechanism that
already gives you `{{ user }}` everywhere via
`django.contrib.auth.context_processors.auth`.

### Ownership checks — 404, not 403

```python
get_object_or_404(Notification, pk=pk, recipient=request.user)
```
A wrong-owner `pk` 404s instead of 403ing — a 403 would confirm the
object *exists*, just isn't yours; a 404 reveals nothing.

---

## Module 15 — Security Best Practices

### OWASP Top 10 quick map (Django's default posture)

| Risk | Django's default defense |
|---|---|
| SQL injection | ORM parameterizes everything; never build raw SQL with f-strings |
| XSS | Templates auto-escape by default; avoid `\|safe`/`mark_safe`, use `format_html()` |
| CSRF | `CsrfViewMiddleware` + `{% csrf_token %}` on every form |
| Broken auth | Password hashing built in; add rate limiting (below) |
| Security misconfiguration | `check --deploy` (below) |
| Sensitive data exposure | `.env` + `.env.example`, never commit secrets |
| Broken access control | Permission classes/mixins; 404 (not 403) for "not yours" |

### check --deploy

```bash
python manage.py check --deploy
```
Runs checks that are OFF by default (too noisy for daily dev), only when
asked. Common findings: `W009` insecure `SECRET_KEY`, `W018` `DEBUG=True`,
`W020` empty `ALLOWED_HOSTS`, `W004/W008/W012/W016` missing HTTPS-only
cookie/HSTS/redirect settings.

### Secrets via .env

```python
# settings.py
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")   # no-op if missing

SECRET_KEY = os.environ.get("SECRET_KEY", "<dev-only fallback>")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
```
`.env` → gitignored, real values. `.env.example` → committed, placeholders.

### Production-only security settings

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000   # start lower (e.g. 3600) the first time on a real domain
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```
Gate on `DEBUG` — these assume HTTPS, which local `runserver` doesn't have.

### DRF throttling

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/minute", "user": "100/minute"},
}
```
Per-endpoint rate (e.g. login): `ScopedRateThrottle` + `throttle_scope = "..."` on the view + a `"scopes"` rate.

**Gotcha:** `SimpleRateThrottle.THROTTLE_RATES` is a class attribute read
from settings ONCE at import time — overriding `DEFAULT_THROTTLE_RATES`
mid-test-suite won't change it if the throttle class already imported
earlier. Test against the real configured rate instead of shrinking it
per-test.

### Upload size validation

```python
def validate_image_size(image_file):
    if image_file.size > MAX_SIZE_BYTES:
        raise ValidationError("Too large.")

image = models.ImageField(upload_to="...", validators=[validate_image_size])
```
An `ImageField` alone only validates it's a real image (via Pillow) —
not that it's a *reasonable size*. No limit = disk-fill/worker-exhaustion
DoS vector, even behind a permission check.

### Settings-resolved-once, again (Module 13 callback)

A conditional block in `settings.py` (`if not DEBUG: ...`) runs exactly
once, using the environment at process startup. Overriding just the
condition later (`settings.DEBUG = False` in a test) does NOT re-run the
block — override every setting the block would have set, individually,
if you need to simulate its effect after the fact.

---

## Module 16 — Configuration, Docker & Deployment

### Env-var-switched settings (same pattern, three times now)

```python
if os.environ.get('POSTGRES_DB'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', ...}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}

if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage"}, ...}
# else: Django's own local-disk default applies
```
No env var → local/SQLite fallback (zero setup). Env var present → the
real backend. Never a separate "Docker settings file."

### Testing a setting resolved once, at import time

```python
def _run_in_subprocess(extra_env):
    return subprocess.run([sys.executable, "-c", PROBE], env={**os.environ, **extra_env}, ...)
```
Only a **fresh process** (env var set before Django imports `settings.py`)
actually exercises a branch like the one above — the `settings` fixture
mid-test can't rewind code that already ran (Modules 13, 15, 16, same lesson).

### Dockerfile essentials

```dockerfile
FROM python:3.12-slim              # not alpine — musl breaks Pillow/psycopg2 wheels
COPY requirements.txt .            # BEFORE the rest of the app — caches the slow layer
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["./docker-entrypoint.sh"]   # always runs first
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]  # compose can override this
```

```sh
#!/bin/sh
set -e
until python manage.py showmigrations > /dev/null 2>&1; do sleep 1; done   # real readiness check, not a ping
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"                           # becomes PID 1 — receives shutdown signals directly
```

### .gitattributes — the Windows line-ending trap

```
*.sh text eol=lf
Dockerfile text eol=lf
```
Without this, `core.autocrlf=true` silently turns `#!/bin/sh` into
`#!/bin/sh\r` on checkout — the container fails with a confusing
"no such file or directory," not an obvious line-ending error.

### docker-compose.yml essentials

```yaml
services:
  web:
    environment:
      POSTGRES_HOST: db            # service name, NEVER localhost
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      db: {condition: service_healthy}
  worker:
    build: .
    command: celery -A config worker --loglevel=info   # overrides CMD, keeps ENTRYPOINT
volumes:
  static_volume:   # shared between web (writes) and nginx (reads)
  media_volume:
```
Containers reach each other by **service name** via Docker's internal
DNS — `localhost` inside a container means that container itself.

### Nginx: static files never touch Django

```nginx
location /static/ { alias /app/staticfiles/; }
location /media/  { alias /app/media/; }
location / { proxy_pass http://web:8000; proxy_set_header Host $host; }
```

### CI against the real database engine

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env: {POSTGRES_DB: atlas_ci, ...}
```
SQLite is lenient about things Postgres isn't — "tests pass on SQLite"
doesn't prove the app works on the database production actually uses.

### Known trade-off: migrations run in every container

`web`/`worker`/`beat` all inherit the same entrypoint, so all three run
`migrate` on startup — simple, but redundant, and a real risk of lock
contention under concurrent schema changes. Production-grade fix: a
single one-off release/migrate step; nothing else runs migrations itself.

---

## Module 17 — Git Workflow, System Design & Job Readiness

### Git workflow (full version: repo-root `CONTRIBUTING.md`)

- **Trunk-based**: short-lived branches (`feat/...`, `fix/...`), merge
  back within days, `main` always deployable.
- **Conventional Commits**: `<type>(<scope>): <imperative summary>` +
  body explaining WHY. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
- **Every change via PR**, even solo/two-person teams — CI must run,
  one other human must look at the diff, no self-merging without review.
- **Reviewer checks**: matches the PR description? tests exist and would
  actually fail without the fix? touches permissions/input/secrets
  (Module 15 checklist)? simplest version of the fix?

### Architecture trade-offs — the pattern to reuse

For every "why did you choose X" question: name the alternative, name
the trade-off, name the CONCRETE trigger that would flip the decision.
"At scale" alone is not an answer.

| Choice made | Alternative | Real trigger to switch |
|---|---|---|
| SQLite (dev) | PostgreSQL (prod) | Concurrent writes (SQLite locks the whole file) |
| LocMemCache | Redis | >1 worker process (each has its own separate cache) |
| Celery | Inline processing | Work whose latency/failure shouldn't block the request |
| Local disk uploads | S3-compatible storage | >1 container replica (disk isn't shared or persistent) |
| Token auth | JWT | Need stateless verification badly enough to accept harder revocation |
| Group permissions | Object-level (django-guardian) | Need to scope access below "everyone in this group" |
| Monolith | Microservices | ONE part needs a genuinely different scaling shape than the rest |
| REST | GraphQL | Multiple clients each needing meaningfully different data shapes |

### Interview questions grounded in Atlas — the shape of a good answer

- **"Walk me through X flow"** → name the actual code path, not a
  generic description (signals, transaction boundaries, what's deferred
  and why).
- **"A bug you fixed"** → a specific failure, a specific root cause, a
  specific test proving the fix — not "I debugged some stuff."
- **"How would you scale this?"** → identify the actual bottleneck
  first; don't reach for "microservices" as a reflex.
- **"How do you know it works?"** → point at the test suite, CI, and any
  specific proof-style test (query counts, timing, deploy checks) — not
  "I tested it manually."
- **"What's not done / what would you change?"** → name something real.
  Honesty about known gaps reads as MORE senior, not less.

### Portfolio presentation

- Resume bullet: outcome + mechanism, not a tool list.
- README = the pitch: name specific mechanisms an interviewer can ask
  follow-up questions about.
- Point at commit history (`git log --oneline`) as evidence of
  incremental, deliberate engineering.
- Have one specific hard problem ready to explain well, end to end.
