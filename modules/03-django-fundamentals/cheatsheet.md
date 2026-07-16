# Cheat Sheet — Module 03: Django Fundamentals

## Commands

```bash
django-admin startproject config .     # new project in the current dir
python manage.py startapp pages        # new app
python manage.py runserver             # dev server, default :8000
python manage.py runserver 8080        # dev server on a specific port
python manage.py migrate               # apply migrations (needed even with no custom models)
python manage.py shell                 # Python shell with Django loaded
```

## Project vs App

| | Project | App |
|---|---|---|
| Count | exactly one | one or more |
| Contains | settings, root urls | views, models, templates for one feature area |
| Example | `config/` | `pages/` |
| Must be registered? | — | yes, in `INSTALLED_APPS` |

## URLs

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

## Path converters

| Converter | Matches | View receives |
|---|---|---|
| `str` (default) | anything except `/` | `str` |
| `int` | digits only | `int` |
| `slug` | letters/numbers/hyphens/underscores | `str` |
| `uuid` | a valid UUID | `UUID` |
| `path` | anything, including `/` | `str` |

## Views

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

## Templates (DTL)

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

## Static files

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

## Request → response, the whole path

```
URL hits config/urls.py
  → include('pages.urls') delegates to pages/urls.py
    → path() matches, calls a view in pages/views.py
      → view calls render(request, template, context)
        → template extends base.html, fills in {% block %}
          → HttpResponse sent back to the browser
```
