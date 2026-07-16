# Module 06 — Forms & Function-Based Views (CRUD)

> **Where we're going:** Atlas gets real, public-facing CRUD for products —
> hand-built forms, server-side validation, and the create/read/update/delete
> pattern you'll implement (in one shape or another) for the rest of your
> Django career. The `catalog` app now owns product management; `pages`
> shrinks back down to Home/About.

## 1. Why not just use the admin for everything?

The admin (Module 05) is a staff-only internal tool. Real customers and
salespeople need pages that look like *your* app, with *your* business rules
and *your* validation messages — that's what we build now, by hand, so you
understand every piece before Module 07 shows you how Django's generic
class-based views automate the repetitive parts.

## 2. Forms — validating and cleaning user input

A Django `Form` describes fields and validation rules, independent of any
model. A `ModelForm` does the same thing but derives its fields from a model
automatically — the far more common case, and what Atlas uses:

```python
# catalog/forms.py
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "category", "supplier", "tags",
                   "description", "price", "cost_price",
                   "quantity_in_stock", "reorder_level", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
```

`fields` is deliberately explicit (not `"__all__"`) — **always list fields
explicitly**. If you add a sensitive field to the model later
(Module 08 will add things like ownership/permission fields), an explicit
list means it's never accidentally exposed to a form just because it exists
on the model.

### Validation: `clean_<field>()` and `clean()`

```python
def clean_price(self):
    price = self.cleaned_data["price"]
    if price <= 0:
        raise forms.ValidationError("Price must be greater than zero.")
    return price

def clean(self):
    cleaned_data = super().clean()
    price = cleaned_data.get("price")
    cost_price = cleaned_data.get("cost_price")
    if price is not None and cost_price is not None and cost_price > price:
        raise forms.ValidationError("Cost price can't be higher than the selling price.")
    return cleaned_data
```

- `clean_<fieldname>()` — validates **one** field; runs after Django's own
  built-in field validation (type conversion, required-ness, etc.) has
  already passed for that field. Must return the cleaned value.
- `clean()` — runs **after** every `clean_<field>()`; use it for rules that
  need **more than one field at once** (like comparing `price` and
  `cost_price`, as above). Must return `cleaned_data`.

We verified both of these actually reject bad input — see §6.

## 3. CSRF protection — why every form needs `{% csrf_token %}`

Cross-Site Request Forgery: without protection, another website could trick
a logged-in user's browser into submitting a form to *your* site (their
browser auto-sends your site's cookies). Django's `CsrfViewMiddleware`
blocks any POST that doesn't include a valid, per-session token — which is
why every `<form method="post">` needs:

```django
<form method="post">
    {% csrf_token %}
    ...
</form>
```

Forget it, and Django rejects the submission with a 403 — this is
deliberate and correct behavior, not a bug to work around.

## 4. The CRUD pattern with function-based views

Five views, one per operation, all in `catalog/views.py`:

```python
def product_list(request):
    products = Product.objects.filter(is_active=True)
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(name__icontains=query)
    return render(request, "catalog/product_list.html", {"products": products, "query": query})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "catalog/product_detail.html", {"product": product})

def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" was created.')
            return redirect("catalog:product_detail", pk=product.pk)
    else:
        form = ProductForm()
    return render(request, "catalog/product_form.html", {"form": form, "is_create": True})
```

Patterns worth internalizing — you'll type variations of these constantly:

- **`get_object_or_404`** — fetch or raise a clean 404, instead of a raw
  `DoesNotExist` exception leaking a stack trace to the user.
- **One view, two methods**: `product_create`/`product_update` handle both
  `GET` (show a blank/pre-filled form) and `POST` (process a submission) in
  the same function, branching on `request.method`.
- **Post/Redirect/Get (PRG)**: after a successful POST, always `redirect(...)`
  to a `GET` URL rather than rendering a template directly. This is why
  refreshing a page after submitting a form doesn't resubmit it — the
  browser's last request was a GET to the detail page, not the original POST.
- **`ModelForm(instance=product)`** — passing `instance=` on `GET`
  pre-fills the form with the existing object's data; passing it again on
  `POST` (`ProductForm(request.POST, instance=product)`) makes `.save()`
  update that same row instead of creating a new one. This single
  difference (`instance=` present or not) is the entire distinction between
  "create" and "update" views.
- **`django.contrib.messages`** — `messages.success(request, "...")` queues
  a one-time notification, rendered on the *next* page (see `{% if messages
  %}` in `templates/base.html`) and then automatically cleared — the
  standard way to say "that worked" after a redirect.

## 5. Wiring it up

```python
# catalog/urls.py
app_name = "catalog"
urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("create/", views.product_create, name="product_create"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("<int:pk>/edit/", views.product_update, name="product_update"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
]
```
```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('products/', include('catalog.urls')),
    path('', include('pages.urls')),
]
```

Note `Product.get_absolute_url()` (defined back in Module 04, pointing at
`catalog:product_detail`) **finally works** now that this URL name exists —
go check `product_list.html`'s `{{ product.get_absolute_url }}` link.

We also **removed** the old `pages:products` demo view/URL/template
entirely — `catalog` is now the single owner of product-related pages.
`pages` shrinks back to just Home and About. This kind of consolidation —
a quick prototype in one place, later promoted to its own properly-owned
app — is completely normal as a real project grows.

## 6. What we verified, for real

Using Django's test `Client` (handles CSRF/session correctly, no manual
cookie wrangling needed):

```
list (empty): 200, shows "add one" link
create form GET: 200, includes a CSRF token
create POST with price=0: 200 (re-rendered), shows "must be greater than zero"
  -> product NOT created
create POST with cost_price > price: 200 (re-rendered), shows the cross-field error
  -> product NOT created
create POST valid: redirected to detail page, "was created" message shown
list now shows the product; ?q=mechanical matches; ?q=nonexistent shows "No products match"
detail page: 200, shows SKU
get_absolute_url(): '/products/1/'          <- now resolves for real
edit form GET: pre-filled with current name
update POST: name changed, "was updated" message shown
delete confirm GET: shows "can't be undone"
delete POST: "was deleted" message shown, product confirmed gone from the database
```

Every one of those is a real assertion against the real running app, not a
description of expected behavior.

## 7. Hands-on

```bash
cd project/atlas
python manage.py runserver
```

Visit `/products/`, then:
1. Click "+ Add product" — try submitting with `price` set to `0` and watch
   the field-level error appear; try `cost_price` higher than `price` and
   watch the form-level error appear at the top.
2. Submit a valid product — notice the success message and the redirect to
   its detail page.
3. Search using `?q=` in the list page.
4. Edit and then delete the product you just created, watching the
   messages each time.

### Exercise

Add a **`customers` CRUD** following the exact same pattern:
`CustomerForm` (ModelForm), `customer_list`/`customer_detail`/
`customer_create`/`customer_update`/`customer_delete` views,
`customers/urls.py` with `app_name = "customers"`, wired into
`config/urls.py` at `path('customers/', include('customers.urls'))`, and
templates mirroring `catalog`'s. Add at least one custom validation rule
(e.g. reject a phone number containing letters).

## 8. Checkpoint — you should now be able to:

- [ ] Explain the difference between `Form` and `ModelForm`.
- [ ] Write a field-level (`clean_<field>`) and a cross-field (`clean()`)
      validator, and explain when each applies.
- [ ] Explain what CSRF protection defends against and why `{% csrf_token %}`
      is required in every POST form.
- [ ] Write a create/update view pair that branches on `request.method` and
      uses `instance=` to distinguish them.
- [ ] Explain the Post/Redirect/Get pattern and why it prevents duplicate
      form submissions on refresh.
- [ ] Use `django.contrib.messages` to show a one-time success notification.
- [ ] Have completed the customers CRUD exercise above, verified in a
      running server.

## 9. What's next

**Module 07 — Class-Based Views** takes this exact CRUD pattern — you just
wrote it by hand, five times, with a lot of repeated structure — and shows
you how Django's generic `ListView`/`DetailView`/`CreateView`/`UpdateView`/
`DeleteView` collapse most of it into a few lines each, while still letting
you override anything you need to customize.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 07.
