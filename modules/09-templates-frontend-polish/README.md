# Module 09 — Templates & Frontend Polish

> **Where we're going:** Atlas gets a real visual pass — Bootstrap 5,
> custom template tags/filters, and a genuine dashboard page with live
> stats — so it stops looking like "a programming exercise" and starts
> looking like a product you'd put in a portfolio.

## 1. Bringing in Bootstrap — no build step needed yet

We add Bootstrap via CDN in `templates/base.html`:

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```

This is a deliberate, honest shortcut: a CDN needs zero tooling, which is
right for where we are in the course. Module 16 covers bundling your own
static assets (and vendoring dependencies) properly for production — you
don't want to depend on a third party's CDN staying up forever for a real
deployed app, but for learning right now, it's the correct trade-off.

`static/css/custom.css` is now intentionally **small** — a handful of
brand-specific overrides (the hero gradient, the logo accent color, stat
card styling) layered *on top of* Bootstrap, instead of hand-rolling every
layout rule ourselves like in Modules 02-08. This is the realistic pattern:
**a framework for structure/components, a thin custom sheet for brand**.

## 2. Custom template filters and tags

Django lets you register your own template logic, importable with
`{% load your_module %}`. Two we added, both real, reusable code:

### A filter: `add_class`

Django's own `{{ form.as_p }}` doesn't know about Bootstrap — its rendered
`<input>` tags have no `class="form-control"`. Rather than edit every
form's widget definitions by hand, one small filter fixes every form,
everywhere:

```python
# pages/templatetags/form_extras.py
from django import template
register = template.Library()

@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
```
```django
{% load form_extras %}
{{ form.name|add_class:"form-control" }}
```

### A filter that had to exist because of a real template language rule

We initially tried checking `field.field.widget.input_type` in the
template to decide which Bootstrap class to apply (`form-control` vs
`form-select` vs `form-check-input`) — and hit two real problems:

1. `input_type` doesn't exist on `Select`, `SelectMultiple`, or `Textarea`
   widgets at all (only genuine `<input>`-based widgets have it) — so the
   check silently resolved to an empty string and gave every field the
   wrong class.
2. The natural Python fix — `field.field.widget.__class__.__name__` —
   **cannot be written in a Django template at all**: Django's template
   language deliberately refuses to resolve any attribute or method
   starting with an underscore, `__class__` included. This is a real,
   documented security/convention rule, not a bug we ran into by accident.

The fix: push that logic into a filter, where it's just plain Python with
no such restriction:

```python
@register.filter
def widget_type(field):
    return field.field.widget.__class__.__name__
```
```django
{% with kind=field|widget_type %}
    {% if kind == "CheckboxInput" %}
        {{ field|add_class:"form-check-input" }}
    {% elif kind == "Select" or kind == "SelectMultiple" %}
        {{ field|add_class:"form-select" }}
    {% else %}
        {{ field|add_class:"form-control" }}
    {% endif %}
{% endwith %}
```

We verified this actually assigns the right class per field type on the
real product form: `category`/`tags` (Select/SelectMultiple) get
`form-select`, `is_active` (checkbox) gets `form-check-input`, everything
else gets `form-control` — see §5.

**General lesson**: templates are intentionally limited (no arbitrary
Python, no underscore access) so that view logic doesn't leak into
presentation. When a template needs something templates can't express
cleanly, that's exactly what a filter or tag is for — don't fight the
template language, extend it.

### A simple_tag: `low_stock_count`

```python
# catalog/templatetags/catalog_extras.py
from django.db.models import F

@register.simple_tag
def low_stock_count():
    return Product.objects.filter(
        is_active=True, quantity_in_stock__lte=F("reorder_level")
    ).count()
```
```django
{% load catalog_extras %}
{% low_stock_count %}
```

`F("reorder_level")` compares two **fields on the same row** inside the
database query itself (`WHERE quantity_in_stock <= reorder_level`), rather
than pulling every product into Python and comparing there — Module 12
covers `F()` expressions and query optimization properly; this is a first
real taste. Also worth flagging honestly: this tag re-runs its query
*every time it's used* (e.g. if it were in the nav on every page) — that's
exactly the kind of repeated-query cost Module 12's caching section exists
to fix. We use it only on the dashboard for now, not globally, for exactly
that reason.

## 3. A real dashboard

```python
# pages/views.py
@login_required
def dashboard(request):
    context = {
        "product_count": Product.objects.filter(is_active=True).count(),
        "low_stock_count": Product.objects.filter(is_active=True, quantity_in_stock__lte=F("reorder_level")).count(),
        "customer_count": Customer.objects.count(),
        "order_count": Order.objects.count(),
        "recent_orders": Order.objects.select_related("customer").order_by("-created_at")[:5],
    }
    return render(request, "pages/dashboard.html", context)
```

- **`@login_required`** — the function-view equivalent of Module 08's
  `LoginRequiredMixin` for class-based views. Same protection, different
  syntax because `pages` still uses function-based views (Module 07 only
  converted `catalog`).
- **`select_related("customer")`** — a first preview of Module 12: without
  it, rendering `order.customer.full_name` for each of the 5 recent orders
  in the template would trigger 5 *extra* database queries (one per order)
  on top of the original one — a classic "N+1 query" problem.
  `select_related` fetches the related `Customer` row in the **same**
  query via a SQL JOIN. We'll measure this difference directly in Module 12.

The template uses Bootstrap's card/grid utilities for stat tiles and the
`currency` filter (also added this module, in `catalog_extras.py`) to
format money consistently everywhere: `{{ order.total|currency }}` →
`$159.98`.

## 4. Template inheritance, one level further

`base.html`'s `{% block content %}` is now wrapped in Bootstrap's
`.container` **in the base template itself**, not repeated in every child
— every page that extends `base.html` (`home.html`, `product_list.html`,
`dashboard.html`, ...) writes its content directly, with no wrapping `<div
class="container">` of its own. This is worth internalizing: **layout that
applies to every page belongs in the base template**, not copy-pasted into
each child — exactly the DRY principle template inheritance exists for.

## 5. What we verified, for real

```
/, /about/, /products/, /products/1/  — all 200
Bootstrap CSS actually linked in the rendered HTML (bootstrap@5.3.3)
custom.css actually linked
currency filter renders "$79.99" correctly

anonymous GET /dashboard/ redirected to login (login_required works on FBVs too)
logged-in GET /dashboard/: 200
  shows product_count correctly
  shows a "Reorder" badge when low_stock_count > 0
  shows the recent order with the customer's name (via select_related)
  order total rendered via the currency filter: "$159.98" (2 x $79.99)

create form: category field gets class="form-select"
             tags field gets class="form-select"
             is_active field gets class="form-check-input"
             name field gets class="form-control"
full create flow still works end-to-end with the new templates,
  success message rendered with Bootstrap's alert-success class
```

## 6. Hands-on

```bash
cd project/atlas
python manage.py runserver
```

Log in and visit `/dashboard/` — add a product with `quantity_in_stock`
below its `reorder_level` and watch the "Low stock" stat and its badge
update. Resize your browser to mobile width and check the navbar collapses
into Bootstrap's hamburger menu (`navbar-toggler`) — that's Bootstrap's JS
bundle doing its job, no code of ours required.

### Exercise

Add a new custom filter, `stock_badge`, that takes a `Product` and returns
a ready-to-use Bootstrap badge HTML snippet (`<span class="badge
bg-success">In stock</span>` or `bg-danger">Out of stock`) — you'll need
`django.utils.safestring.mark_safe` (or the `@register.filter(is_safe=True)`
option) since the filter returns HTML, not plain text; look up why Django
escapes filter output by default before using it (this is exactly what
Module 15's XSS section explains in depth — for now, just get it working
and note *why* `mark_safe` is needed). Use it to simplify the stock badge
markup in `product_list.html` and `product_detail.html`.

## 7. Checkpoint — you should now be able to:

- [ ] Explain why layout common to every page belongs in `base.html`, not
      each child template.
- [ ] Write a custom template filter and register/load it correctly.
- [ ] Explain why Django templates refuse underscore-prefixed attribute
      access, and why that pushes some logic into filters/tags instead.
- [ ] Write a `simple_tag` and explain the cost of calling it on every
      page (a fresh query each time).
- [ ] Explain what `select_related` does and why skipping it here would
      cause extra queries.
- [ ] Have completed the `stock_badge` exercise above.

## 8. What's next

**Module 10 — Django REST Framework** takes everything Atlas can already
do through HTML pages and exposes it as a **JSON API** — the same
`Product`/`Customer`/`Order` models, now consumable by a mobile app, a
JavaScript frontend, or another service entirely, with its own
authentication and permission model built on Django REST Framework.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 10.
