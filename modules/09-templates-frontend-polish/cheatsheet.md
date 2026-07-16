# Cheat Sheet — Module 09: Templates & Frontend Polish

## Bootstrap via CDN

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```
Fine for learning/dev; Module 16 covers bundling your own static assets for production.

## Custom template filter

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

## Custom simple_tag

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

## Django templates forbid underscore attribute access

`{{ obj.__class__ }}` never works — silently resolves to nothing. Need a
Python-side attribute lookup? Write a filter:
```python
@register.filter
def widget_type(field):
    return field.field.widget.__class__.__name__
```

## F() expressions — compare two fields in the database

```python
from django.db.models import F
Product.objects.filter(quantity_in_stock__lte=F("reorder_level"))
```

## select_related — avoid N+1 queries across a FK

```python
Order.objects.select_related("customer").order_by("-created_at")[:5]
```
Without it: 1 query for orders + 1 extra query per order to fetch
`.customer`. With it: 1 query total (SQL JOIN). Deep dive in Module 12.

## login_required (function-based view equivalent of LoginRequiredMixin)

```python
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    ...
```

## Layout that applies to every page → base.html, not every child

```django
<!-- base.html -->
<div class="container">
    {% block content %}{% endblock %}
</div>
```
Child templates write content directly — no repeated `<div class="container">`.

## Returning HTML from a filter (needs mark_safe — see Module 15 for why)

```python
from django.utils.safestring import mark_safe

@register.filter
def stock_badge(product):
    if product.in_stock:
        return mark_safe('<span class="badge bg-success">In stock</span>')
    return mark_safe('<span class="badge bg-danger">Out of stock</span>')
```
