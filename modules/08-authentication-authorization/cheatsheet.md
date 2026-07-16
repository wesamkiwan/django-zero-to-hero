# Cheat Sheet — Module 08: Authentication, Authorization & Permissions

## Custom User model (set up BEFORE the first migrate!)

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

## Login / logout / signup

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

## Settings

```python
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'pages:home'
LOGOUT_REDIRECT_URL = 'pages:home'
```

## Permissions & groups

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

## Seeding a group via data migration

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

## Checking permissions in Python

```python
user.has_perm("catalog.add_product")
user.groups.add(some_group)
user.is_superuser        # bypasses ALL permission checks
```
