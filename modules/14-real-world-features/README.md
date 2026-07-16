# Module 14 — Real-World Features

> **Where we're going:** four features almost every production Django app
> ends up needing, none of them exotic: letting users upload a file,
> generating a PDF on demand, exporting filtered data as a spreadsheet,
> and giving staff an in-app notification when something happens. Each
> one is small in isolation — the value here is seeing all four wired
> into one real app correctly, including the permission questions each
> one raises that a tutorial in isolation wouldn't hit.

## 1. File/image uploads

A `Product` needing a photo means a new field type, plus two settings
Atlas has never needed before:

```python
# catalog/models.py
image = models.ImageField(upload_to="products/", blank=True, null=True)
```

`blank=True` (form-optional) *and* `null=True` (DB-optional) — an empty
`ImageField` is normally stored as `''`, not `NULL`; `null=True` lets a
product genuinely have "no image" instead of an empty-string stand-in.
`ImageField` (rather than plain `FileField`) additionally validates the
upload is really an image, using Pillow — hence `Pillow` joining
`requirements.txt`.

```python
# settings.py
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

`MEDIA_*` is a **second**, separate concept from `STATIC_*`: static files
ship *with* your code (CSS, JS); media files are uploaded by users at
runtime and don't belong in version control at all — `media/` is already
in `.gitignore`.

```python
# config/urls.py
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Django never serves media files itself outside of `DEBUG` — a real
deployment hands that job to Nginx or object storage (Module 16) instead,
since a Python process serving raw files is slow and a security risk if
misconfigured.

The one line every tutorial forgets, and the one that actually matters:

```html
<!-- templates/catalog/product_form.html -->
<form method="post" enctype="multipart/form-data">
```

Without `enctype="multipart/form-data"`, a browser silently submits the
file field as empty — no error, the request just doesn't contain the
file. Django's `CreateView`/`UpdateView` already pass `request.FILES`
into the form for you (`FormMixin.get_form_kwargs()` does this
automatically on POST); the form tag is the only thing you have to
remember yourself.

```python
def test_creating_a_product_with_an_image_saves_and_serves_it(client, sales_rep_user, category):
    ...
    response = client.post(reverse("catalog:product_create"), {..., "image": _tiny_image()})
    product = Product.objects.get(sku="PW-001")
    assert product.image.read() == TINY_GIF   # the actual bytes round-trip, not just a filename
```

`TINY_GIF` is the smallest valid GIF that exists (a hand-written 1×1
transparent pixel, as raw bytes) — enough for Pillow to accept it as a
real image without a binary fixture file living in the repo. Tests that
create images need one more piece of setup, in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def _tmp_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
```

Without this, every image-saving test would write a real file into
`project/atlas/media/` — accumulating orphaned test images in the same
directory real uploads use. `tmp_path` (built into pytest) is a fresh,
auto-cleaned-up directory per test; the `settings` fixture (from
pytest-django) reverts the override once the test ends.

## 2. PDF invoice generation

```python
# orders/views.py
@login_required
@permission_required("orders.view_order", raise_exception=True)
def order_invoice_pdf(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("items__product"), pk=pk)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    # ... draw text/table onto pdf via pdf.drawString(x, y, "...") ...
    pdf.showPage()
    pdf.save()

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="order-{order.pk}-invoice.pdf"'
    return response
```

Built with `reportlab`, generated **on demand** rather than stored as a
file per order — cheap to build, and it can never go stale the way a
pre-rendered file would (edit an `OrderItem`, the next download reflects
it automatically). `io.BytesIO()` is an in-memory buffer standing in for
a file — `reportlab` writes the PDF into it without touching disk at all,
and `HttpResponse` reads it straight back out.

Notice this view uses function-based `@login_required`/`@permission_required`
decorators rather than the CBV `LoginRequiredMixin`/`PermissionRequiredMixin`
pattern `catalog/views.py` uses — same underlying check, different syntax,
because this one's a plain function, not a class. Both are completely
normal Django; which you reach for depends on whether generic CBV
behavior (`ListView`, `CreateView`, ...) is buying you anything, and here
there's no generic view for "build a PDF" to inherit from.

**A permission gap this surfaced:** nobody but a superuser could view an
`Order` at all before this module — the "Sales Team" group (Module 08)
only ever granted `Product` permissions. `orders/migrations/0002_grant_sales_team_view_order.py`
adds `view_order` to that same group, the same `get_or_create()`-based
data migration pattern as the original group setup, so this feature has
a real permission to gate on instead of falling back to
superuser-only or, worse, no check at all.

```python
def test_customer_role_cannot_view_invoice(client, customer_user, order):
    client.force_login(customer_user)
    response = client.get(reverse("orders:invoice_pdf", args=[order.pk]))
    assert response.status_code == 403

def test_sales_rep_can_download_invoice_pdf(client, sales_rep_user, order, product):
    ...
    assert response.content.startswith(b"%PDF")   # a real, well-formed PDF, not an error page
```

`%PDF` is the literal first four bytes of every valid PDF file (its
"magic number") — asserting on it proves reportlab actually produced a
real document, not just *a* 200 response with the right `Content-Type`
header and garbage inside.

## 3. CSV export

```python
# catalog/views.py
def product_export_csv(request):
    qs = _filter_products(request, Product.objects.select_related("category", "supplier").filter(is_active=True))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(["SKU", "Name", "Category", "Price", "Quantity in stock", "Needs reorder"])
    for product in qs:
        writer.writerow([product.sku, product.name, product.category.name, product.price, product.quantity_in_stock, product.needs_reorder()])
    return response
```

Two things worth noticing:

- **No new dependency.** `csv` is in the Python standard library, and
  `csv.writer` happily writes straight to an `HttpResponse` — a response
  object implements enough of the file-like `.write()` protocol for
  `csv.writer` not to know the difference.
- **`_filter_products(request, qs)` is shared** between
  `ProductListView.get_queryset()` and this view — the exact same
  search/category/stock filtering logic, extracted so "export" always
  means "exactly what this URL's filters currently show," not a second
  copy of the filtering rules that can quietly drift out of sync with
  the first.

```python
def test_export_csv_respects_search_filter(client, category):
    ProductFactory(name="Mechanical Keyboard", sku="MK-1", category=category)
    ProductFactory(name="Wireless Mouse", sku="WM-1", category=category)
    response = client.get(reverse("catalog:product_export_csv"), {"q": "keyboard"})
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    assert [row[0] for row in rows[1:]] == ["MK-1"]
```

The Django admin gets the same feature via an **action** instead of a
standalone view — the standard way admins expose bulk operations on
whatever rows a staff user selected in the list:

```python
# catalog/admin.py
@admin.action(description="Export selected as CSV")
def export_as_csv(modeladmin, request, queryset):
    ...
    for product in queryset.select_related("category"):
        writer.writerow([...])
    return response

class ProductAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive, export_as_csv]
```

## 4. Search & filtering, extended

Module 12 added `Q`-based search across name/SKU/description. This module
adds two more filters — category and stock status — to **both** frontends
that already existed, keeping them consistent:

```python
# catalog/views.py — shared by the web view and the CSV export
def _filter_products(request, qs):
    ...
    category_id = request.GET.get("category", "").strip()
    if category_id:
        qs = qs.filter(category_id=category_id)

    stock = request.GET.get("stock", "").strip()
    if stock == "low":
        qs = qs.filter(quantity_in_stock__lte=F("reorder_level"))
    elif stock == "out":
        qs = qs.filter(quantity_in_stock=0)
    return qs
```

```python
# catalog/api_views.py — ProductViewSet.get_queryset(), same rule, DRF's query_params instead of GET
stock = self.request.query_params.get("stock")
if stock == "low":
    qs = qs.filter(quantity_in_stock__lte=F("reorder_level"))
elif stock == "out":
    qs = qs.filter(quantity_in_stock=0)
```

The web template preserves the current filters across pagination links
(`?page=2&category=3&stock=low`) — a common, easy-to-miss bug is a
filtered list whose "Next" link silently drops the filter on page 2.

## 5. In-app notifications

The last feature is a small new app, `notifications`, because a
notification isn't really *about* products or orders — it's its own
concern that other apps plug into.

```python
# notifications/models.py
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]   # -pk as a tiebreaker — see below
```

Deliberately **not** tied to `Customer`: Customers in this CRM aren't
necessarily site accounts at all (Module 04 never gave `Customer` a `User`
FK), so there'd be nowhere to actually show a Customer a notification.
This app notifies **staff** — managers and sales reps — instead.

`ordering = ["-created_at", "-pk"]`, not just `["-created_at"]`: two
notifications created microseconds apart can land on the *same*
`auto_now_add` value depending on the database's datetime precision,
which would make sort order silently non-deterministic under exactly the
conditions a test creates them in (back-to-back, no delay). `-pk` breaks
the tie using insertion order, which is always unique.

```python
# orders/signals.py — a SECOND receiver on the same signal as Module 13's email
@receiver(post_save, sender=Order)
def notify_managers_of_new_order(sender, instance, created, **kwargs):
    if not created:
        return
    User = get_user_model()
    managers = User.objects.filter(Q(role=User.Role.MANAGER) | Q(is_superuser=True))
    Notification.objects.bulk_create([
        Notification(recipient=m, message=f"New order #{instance.pk} placed by {instance.customer.full_name}.", ...)
        for m in managers
    ])
```

Multiple `@receiver`s can listen to the exact same signal — Django calls
every one of them. This one runs **directly**, with no
`transaction.on_commit()`/Celery involved, unlike Module 13's
confirmation email: it doesn't need `OrderItem`s to exist yet (the
message doesn't mention a total), and it's a plain local database write,
not a slow external call — there's nothing here worth deferring.

Surfacing it everywhere, without every view remembering to fetch it, is
a **context processor** — new this module:

```python
# notifications/context_processors.py
def unread_count(request):
    if not request.user.is_authenticated:
        return {}
    return {"unread_notification_count": Notification.objects.filter(recipient=request.user, is_read=False).count()}
```

```python
# settings.py — TEMPLATES[0]['OPTIONS']['context_processors']
'notifications.context_processors.unread_count',
```

Once registered, `{{ unread_notification_count }}` is available in
**every** template automatically — which is exactly how
`django.contrib.auth.context_processors.auth` has been giving you
`{{ user }}` everywhere since Module 03, without you ever noticing it was
a context processor. `base.html`'s navbar bell just reads the variable:

```html
<a href="{% url 'notifications:list' %}">
    Notifications
    {% if unread_notification_count %}<span class="badge bg-danger">{{ unread_notification_count }}</span>{% endif %}
</a>
```

```python
def test_user_only_sees_their_own_notifications(client):
    me, someone_else = UserFactory(), UserFactory()
    NotificationFactory(recipient=me, message="Mine")
    NotificationFactory(recipient=someone_else, message="Not mine")
    client.force_login(me)
    response = client.get(reverse("notifications:list"))
    assert b"Mine" in response.content
    assert b"Not mine" not in response.content
```

`NotificationListView.get_queryset()` filters by
`recipient=self.request.user` unconditionally — never by anything the
client sends — so there's no ID to guess to see someone else's
notifications. `mark_read(request, pk)` applies the same rule via
`get_object_or_404(Notification, pk=pk, recipient=request.user)`: a
wrong-owner `pk` doesn't leak a 403 (which would confirm the notification
*exists*, just isn't yours) — it 404s, exactly as if it didn't exist.

## 6. Hands-on

```bash
cd project/atlas
pip install -r requirements-dev.txt   # + Pillow, reportlab
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

- Add a product with an image at `/products/create/`, then view it at
  `/products/<id>/` and in the admin list.
- Place an order via `/api/orders/`, log in as a manager, and check the
  bell icon at `/notifications/`.
- Download an invoice at `/orders/<id>/invoice/` (as a sales rep or
  manager — try it as a plain customer role first and confirm the 403).
- Try `/products/export/?stock=low` and open the download in a
  spreadsheet app.

### Exercise

Add a `Notification` for the **customer's assigned sales rep** (not just
managers) when an order's `status` changes to `"shipped"` — you'll need a
way to know which sales rep "owns" a given order, which doesn't exist
yet; as a design question (no code required), would you add that as a
field on `Order`, on `Customer`, or somewhere else, and why?

## 7. Checkpoint — you should now be able to:

- [ ] Add an `ImageField`, wire up `MEDIA_URL`/`MEDIA_ROOT`, and explain
      why `enctype="multipart/form-data"` is required and easy to forget.
- [ ] Explain why test image uploads need a temporary `MEDIA_ROOT`.
- [ ] Generate a PDF on demand with `reportlab` and stream it back via
      `HttpResponse` without touching disk.
- [ ] Explain why a permission check surfaced a real gap in this app's
      existing group permissions, and fix it with a data migration.
- [ ] Export a filtered queryset as CSV using the standard library,
      reusing the same filtering logic a list view already has.
- [ ] Explain what a context processor is and register one.
- [ ] Have completed the sales-rep notification exercise above.

## 8. What's next

**Module 15 — Security Best Practices** turns a critical eye on
everything built so far: the OWASP Top 10 in a Django context, settings
that are fine for a course but wrong for production (that hardcoded
`SECRET_KEY`, `DEBUG = True`), and managing secrets properly instead of
committing them.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 15.
