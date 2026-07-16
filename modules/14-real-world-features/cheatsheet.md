# Cheat Sheet — Module 14: Real-World Features

## File/image uploads

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

## PDF generation (reportlab)

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

## CSV export (standard library, no dependency)

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

## Filtering (extends Module 12's Q search)

```python
qs.filter(category_id=category_id)
qs.filter(quantity_in_stock__lte=F("reorder_level"))   # "low" stock
qs.filter(quantity_in_stock=0)                          # "out" of stock
```
Preserve every active filter across pagination links, not just the search term.

## Permission gaps surfaced by a new feature

A new view needing `app.view_model` doesn't mean that permission exists
on any group yet — check, and add a data migration if not (same pattern
as `accounts/migrations/0002_create_sales_team_group.py`):
```python
group.permissions.add(Permission.objects.get_or_create(
    content_type=ContentType.objects.get_or_create(app_label="orders", model="order")[0],
    codename="view_order", defaults={"name": "Can view order"},
)[0])
```

## Notifications app

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

## Context processors

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

## Ownership checks — 404, not 403

```python
get_object_or_404(Notification, pk=pk, recipient=request.user)
```
A wrong-owner `pk` 404s instead of 403ing — a 403 would confirm the
object *exists*, just isn't yours; a 404 reveals nothing.
