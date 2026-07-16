# Module 08 — Authentication, Authorization & Permissions

> **Where we're going:** right now, *anyone* can create, edit, or delete any
> Atlas product with no login at all — that ends here. Atlas gets a custom
> `User` model with roles, real sign up/login/logout, and Django's built-in
> permission system actually gating the CRUD views from Module 06/07.

## 1. Authentication vs. authorization — two different questions

- **Authentication**: "who are you?" — logging in, sessions, `request.user`.
- **Authorization**: "are you allowed to do *this*?" — permissions, groups,
  roles.

Django ships a complete, battle-tested system for both
(`django.contrib.auth`) — you rarely need to hand-roll password hashing,
session handling, or login views yourself, and you shouldn't.

## 2. Why a custom User model, and why it must happen *now*

Django's official docs strongly recommend **every project** define its own
`User` model — even one identical to the default — from its very first
migration, because swapping it in later is painful. We just proved this
ourselves:

We took a copy of Atlas *as it stood after Module 07* (already migrated,
with the default `django.contrib.auth.User`), added a custom `User` model
the way you'd naively expect to, and ran `migrate` again. Real result:

```
django.db.migrations.exceptions.InconsistentMigrationHistory:
Migration admin.0001_initial is applied before its dependency accounts.0001_initial
on database 'default'.
```

Why: `django.contrib.admin`'s own migrations create a `LogEntry` model with
a foreign key to `settings.AUTH_USER_MODEL`. Once that migration is
**applied** against the *old* user model, Django can no longer cleanly slot
a *new* `accounts.0001_initial` in *before* it — but that's exactly the
order required, since the FK depends on the user model existing first.

**In this course**, Atlas is a learning project with no real production
data, so the fix is simple and honest: if you already ran `migrate` in
Modules 04-07, **delete your local `db.sqlite3`** before continuing, and
run `migrate` fresh from scratch after adding `accounts`. In a real
production project, you would **not** have this option — this is precisely
why the rule is "decide your User model before the first migration," not
"swap it in whenever you get around to it."

## 3. The custom User model

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

    @property
    def is_manager(self):
        return self.is_superuser or self.role == self.Role.MANAGER

    @property
    def is_sales_rep(self):
        return self.is_manager or self.role == self.Role.SALES_REP
```

`AbstractUser` already provides `username`, `email`, `password` (hashed),
`is_active`, `is_staff`, `is_superuser`, groups, and permissions — we're
only *adding* `role` on top, not reimplementing authentication.

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

This single line is what makes Django's entire auth system (login, admin,
`request.user`, permissions, everything) use *our* model instead of the
built-in one. `accounts` must appear in `INSTALLED_APPS`, obviously.

## 4. Sign up, log in, log out

Django ships `LoginView`/`LogoutView` — you almost never write these by
hand:

```python
# accounts/urls.py
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

`registration/login.html` is Django's **conventional** default template
path for `LoginView` — using it means you don't even need
`template_name=` (we set it explicitly here just to be unambiguous).

There's no built-in sign-up view (Django doesn't assume every site wants
public registration), so we write one — a thin `CreateView` around
`UserCreationForm`:

```python
# accounts/forms.py
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")   # deliberately NOT "role" — see below
```

```python
# accounts/views.py
from django.contrib.auth import login
from django.views.generic import CreateView

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("pages:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)   # log them in immediately
        return response
```

**`role` is deliberately excluded** from the sign-up form. Every public
sign-up becomes a `Customer` (the model's `default`) — nobody can grant
themselves `Manager` by editing form data. Promotion to Sales Rep/Manager
happens only through the admin, by someone who already has that authority.
This is a real security principle, not an accident: **never let a public
form set fields that grant privilege.**

**Logout is a POST, not a GET**, in modern Django (`LogoutView` has only
accepted POST since Django 4.1) — logging out changes state (ends your
session), and GET requests are supposed to be side-effect-free (Module 02).
See `templates/base.html`'s logout `<form method="post">` with its own
`{% csrf_token %}`.

## 5. Authorization: Django's permission system

Django automatically creates **four permissions per model** the moment
it's registered: `add_<model>`, `change_<model>`, `delete_<model>`,
`view_<model>` (e.g. `catalog.add_product`). A user has a permission if:
- they're a superuser (bypasses all checks), **or**
- the permission is assigned directly to them, **or**
- the permission is assigned to a **group** they belong to.

Groups are the practical unit of authorization in any real project — you
assign permissions to a group once, then add/remove users from it, instead
of managing permissions per-user.

### Seeding a group via a data migration

```python
# accounts/migrations/0002_create_sales_team_group.py
def create_sales_team_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    product_ct, _ = ContentType.objects.get_or_create(app_label="catalog", model="product")
    permissions = [
        Permission.objects.get_or_create(
            content_type=product_ct, codename=f"{action}_product",
            defaults={"name": f"Can {action} product"},
        )[0]
        for action in ("add", "change", "delete")
    ]
    group, _ = Group.objects.get_or_create(name="Sales Team")
    group.permissions.set(permissions)
```

**The gotcha we hit and fixed**: querying for these permissions with a
plain `Permission.objects.get(...)` *fails* here — Django normally creates
them via a `post_migrate` **signal**, which doesn't fire until the *entire*
`migrate` run finishes, too late for a data migration running in the
*middle* of that same run. The fix is `get_or_create()` instead of `get()`
— create them ourselves if they don't exist yet, rather than assuming
they already do. This is a real, documented Django gotcha, not something
we invented for this lesson.

### Enforcing it on views

```python
# catalog/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "catalog.add_product"
    ...

class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "catalog.change_product"
    ...

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "catalog.delete_product"
    ...
```

- **`LoginRequiredMixin`** — redirects anonymous users to `LOGIN_URL`
  (`settings.LOGIN_URL = 'accounts:login'`), with `?next=` set so they land
  back where they were headed after logging in.
- **`PermissionRequiredMixin`** — if logged in but lacking the permission,
  raises `PermissionDenied` (a 403), rather than silently redirecting —
  the user is identified, they're just not allowed to do this.
- **Mixin order matters**: put `LoginRequiredMixin` **before**
  `PermissionRequiredMixin`, both **before** the actual generic view class.
  Python resolves left-to-right, so authentication is checked before
  authorization.
- Note `ProductListView`/`ProductDetailView` have **no** mixins — viewing
  products stays public. Only mutating operations are gated.

### Reflecting permissions in templates

Django automatically exposes a `perms` object in every template:

```django
{% if perms.catalog.add_product %}
    <a href="{% url 'catalog:product_create' %}" class="btn">+ Add product</a>
{% endif %}
```

`product_list.html` and `product_detail.html` both hide Edit/Delete/Add
links from users who can't use them — this is a UX nicety, **not** the
real security boundary (that's the view-level mixins above; a user could
still `POST` directly to the URL, which is exactly what the mixins block).
**Never rely on hiding a button as your only protection.**

## 6. What we verified, for real

```
Sales Team perms (from the data migration): ['add_product', 'change_product', 'delete_product']

signup GET: 200, has CSRF token
signup POST: 200, new user auto-logged in, role defaults to 'customer', is_staff: False

anonymous GET /products/create/: redirected to /accounts/login/
logged-in customer (no permission) GET /products/create/: 403 Forbidden
customer's product list: visible, but NO "Add product" link shown

after adding the user to the "Sales Team" group:
  same user GET /products/create/: 200 (now allowed)
  product list now shows the "Add product" link

superuser GET /products/create/: 200 (superusers bypass permission checks entirely)

logout POST: 200, nav shows "Log in" again
after logout, GET /products/create/: redirected to login again
```

Every line is a real assertion against the running app — the exact same
user, before and after being added to a group, genuinely gains access.

## 7. Hands-on

```bash
cd project/atlas
# if you'd already run migrate before this module, delete your local db first:
rm db.sqlite3     # (or just delete the file in your file browser)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

1. Visit `/accounts/signup/`, create an account — notice you're immediately
   logged in and redirected home, and the nav now shows your username/role
   and a Log out button instead of Log in/Sign up.
2. Try `/products/create/` as this new (Customer) account — you should get
   a 403 page, and no "Add product" link appears in the nav or list.
3. Log into `/admin/` as your superuser, go to **Groups**, confirm the
   "Sales Team" group already exists with its three product permissions
   (seeded by the migration — you didn't create it by hand).
4. Add your test account to that group (via the admin's user edit page),
   log back in as that account, and confirm you can now create/edit/delete
   products.

### Exercise

Add a **"Manager" group** (via a new data migration, mirroring the pattern
above) that also includes `catalog.view_product` explicitly plus
permissions on the `customers` app's `Customer` model (assuming you built
that CRUD in Module 06/07's exercises). Then update
`User.is_manager`-gated logic somewhere real: for example, only show a
"Reports" nav link (even just a placeholder page) to users where
`user.is_manager` is `True`.

## 8. Checkpoint — you should now be able to:

- [ ] Explain the difference between authentication and authorization.
- [ ] Explain why a custom `User` model must be set up before the first
      migration, and what actually breaks if you do it later.
- [ ] Wire up `LoginView`/`LogoutView` and write a custom sign-up view
      around `UserCreationForm`.
- [ ] Explain why sign-up forms should never expose a privilege-granting
      field like `role` directly.
- [ ] Explain Django's four auto-created per-model permissions and how
      groups relate to them.
- [ ] Gate a CBV with `LoginRequiredMixin` + `PermissionRequiredMixin`, in
      the correct order.
- [ ] Use `{% if perms.app.codename %}` in a template, while understanding
      it is *not* a substitute for view-level enforcement.
- [ ] Have completed the Manager group exercise above.

## 9. What's next

**Module 09 — Templates & Frontend Polish** goes back to the UI layer now
that Atlas has real accounts and roles: template inheritance beyond the
basics, custom template tags/filters, and a proper visual pass (Bootstrap
integration) so Atlas starts looking like a real product, not a
programming exercise.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 09.
