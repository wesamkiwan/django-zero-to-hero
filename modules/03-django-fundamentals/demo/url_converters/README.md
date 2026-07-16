# Demo: URL path converters

Atlas's `pages/urls.py` only uses plain string paths so far. In real projects
you constantly need URLs like `/products/42/` or `/orders/<uuid>/`, and want
Django to both **validate** the shape and **convert the type** for you
automatically. This tiny project proves each built-in converter really does
what it claims — run it yourself:

```bash
python -m venv venv
venv\Scripts\Activate.ps1   # or: source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Then try:

| URL | Converter | Result |
|---|---|---|
| `/products/42/` | `<int:product_id>` | `product_id = 42 (type: int)` |
| `/products/abc/` | `<int:product_id>` | **404** — "abc" isn't digits, doesn't match |
| `/categories/office-supplies/` | `<slug:category_slug>` | `category_slug = 'office-supplies'` |
| `/orders/550e8400-e29b-41d4-a716-446655440000/` | `<uuid:order_id>` | a real `UUID` object, not a string |
| `/files/invoices/2026/march.pdf/` | `<path:subpath>` | matches slashes too: `'invoices/2026/march.pdf'` |

## The point

- `<int:...>`, `<slug:...>`, `<uuid:...>` etc. act as **both** a validator
  (won't match the wrong shape — instant 404 instead of your view code
  having to check) **and** a type converter (your view receives a real
  `int`/`UUID`, not a string you'd have to parse yourself).
- `<str:...>` (the default, same as no converter at all) matches anything
  except a `/`.
- `<path:...>` is the only one that matches `/` — useful for genuinely
  wildcard/catch-all routes.

Full list of built-in converters:
https://docs.djangoproject.com/en/stable/topics/http/urls/#path-converters
