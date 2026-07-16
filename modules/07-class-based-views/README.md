# Module 07 — Class-Based Views & Generic Views

> **Where we're going:** we take the five function-based views you hand-wrote
> in Module 06 and refactor them into Django's generic class-based views
> (CBVs) — same URLs, same templates, same behavior, dramatically less code.
> You'll see exactly what each generic view automates and what it still
> lets you override.

## 1. Why class-based views exist

Module 06's `product_create` and `product_update` were almost identical:
check `request.method`, build a form (bound or unbound, with or without
`instance=`), validate, save, message, redirect. That repetition — across
every model in every app — is exactly what CBVs exist to eliminate.

A **class-based view** is a class with methods like `get()` and `post()`
instead of one function branching on `request.method`. Django ships
**generic views** — pre-written CBVs for the standard CRUD operations — so
common cases need almost no code at all.

```python
urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
]
```

`.as_view()` is what actually makes a class usable as a view — it returns a
function that Django's URL dispatcher can call, which internally
instantiates your class fresh for each request and dispatches to the right
method (`get`, `post`, etc.) based on `request.method`. This is why CBVs are
safe under concurrent requests despite being "classes" — a new instance is
created every time.

## 2. The five generic views, mapped to what you already wrote

| Generic view | Replaces | What it needs from you |
|---|---|---|
| `ListView` | `product_list` | `model` (or `get_queryset()`) |
| `DetailView` | `product_detail` | `model` |
| `CreateView` | `product_create` | `model` + `form_class` |
| `UpdateView` | `product_update` | `model` + `form_class` |
| `DeleteView` | `product_delete` | `model` |

Compare `catalog/views.py` now to its Module 06 version (`git log -p` or
your editor's history) — every generic view below replaces roughly 10-15
lines of hand-written branching logic with a handful of class attributes
and, at most, a couple of small method overrides.

### ListView — with search AND pagination for free

```python
class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context
```

- Overriding `get_queryset()` is how you customize *which* objects show up
  — the search logic from Module 06 moved here unchanged.
- `get_context_data()` is how you add **extra** template variables beyond
  the object list — always call `super().get_context_data(**kwargs)` first
  and add to what it returns, never replace it.
- `paginate_by = 12` — **one line** gets you working pagination
  (`page_obj`, `is_paginated`, `?page=2` handling) that would otherwise be
  meaningful hand-written logic. See it working in
  `templates/catalog/product_list.html`'s pagination block.

### DetailView — needs almost nothing

```python
class ProductDetailView(DetailView):
    model = Product
```

That's the entire view. It fetches by the `pk` from the URL, 404s if
missing (exactly like `get_object_or_404` did by hand), and — this is the
convention-over-configuration payoff — **automatically looks for
`catalog/product_detail.html`** (`<app_label>/<model_name>_detail.html`).
Our template was already named exactly that in Module 06, so **zero
template changes were needed** switching to this CBV.

### CreateView / UpdateView — `form_valid()` is your hook

```python
class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'"{self.object.name}" was created.')
        return response
```

- `form_valid(form)` is called **only** when the submitted form passes
  validation — this is where "what happens after a successful save" goes.
  `super().form_valid(form)` does the actual `form.save()` and builds the
  redirect response; you add the message, then return that response
  unchanged.
- **Invalid** submissions are handled automatically too: Django calls
  `form_invalid(form)` (the default implementation just re-renders the
  form with errors) — this is exactly the "re-render with error" behavior
  Module 06 wrote by hand, now free.
- Notice **no `success_url` is set** on either view. `CreateView`/
  `UpdateView` fall back to `self.object.get_absolute_url()` automatically
  when `success_url` is absent — this is *exactly* why Module 04 had you
  define `get_absolute_url()` on `Product` even before any view used it.
  That single method now drives the redirect for both views, with zero
  extra configuration.

### DeleteView — the one that needs a small override

```python
class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("catalog:product_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'"{name}" was deleted.')
        return HttpResponseRedirect(success_url)
```

`DeleteView` has no natural "get_absolute_url after deletion" (the object no
longer exists!), so `success_url` must be set explicitly. Note
**`reverse_lazy`**, not `reverse`: `reverse_lazy` defers resolving the URL
until it's actually *used*, not when the class body executes at import
time — at import time, Django's URLconf may not have finished loading yet,
so eagerly calling `reverse()` here could fail. **Rule of thumb: use
`reverse_lazy` in class attributes, `reverse` inside methods/functions**
(where the URLconf is guaranteed already loaded).

We override `delete()` (rather than relying purely on defaults) for one
reason only: to insert the success message before redirecting — everything
else about deletion is still the built-in behavior.

## 3. What generic views are actually built from

`ListView`, `DetailView`, etc. aren't magic — they're built from small,
reusable **mixins**, combined via multiple inheritance. `CreateView`, for
instance, is roughly `SingleObjectMixin + FormMixin + ProcessFormView`.
You don't need to memorize the mixin hierarchy to use generic views, but
knowing they're "just" composed classes explains *why* overriding one method
(`get_queryset`, `get_context_data`, `form_valid`, `get_success_url`, ...)
changes exactly one piece of behavior without you having to reimplement the
rest — you're overriding one method in a chain, not replacing the whole class.

## 4. When to still write a function-based view

CBVs are a great default for standard CRUD. Reach for a plain function view
when the logic doesn't map cleanly onto "fetch object(s), render/process a
form" — a webhook receiver, a one-off redirect, a view that does several
unrelated things based on complex branching. Don't force a CBV where a
five-line function view is clearer — the goal is less code *and* more
clarity, not CBVs as a rule.

## 5. What we verified, for real

Same rigor as every module — Django's test `Client` against the real,
running CBV-based views:

```
list page 1: 200, is_paginated: True, "Page 1 of 2" shown       (12 per page, 15 seeded)
list page 2: 200, shows the remaining products
create POST (valid): redirected to /products/16/  <- from get_absolute_url(), automatically
"was created" message shown
create POST (invalid, price=0): 200, re-rendered with "must be greater than zero"
update POST: redirected to /products/16/ again, "was updated" shown
delete POST: message shown, product confirmed deleted from the database
search (?q=...): still works, via the overridden get_queryset()
```

Every generic view behaves identically to its Module 06 hand-written
counterpart, plus pagination, for a fraction of the code.

## 6. Hands-on

```bash
cd project/atlas
python manage.py runserver
```

Seed more than 12 products (via `/products/create/` a bunch of times, or the
shell) and visit `/products/` — you'll see real pagination controls at the
bottom. Confirm search still narrows results across paginated pages.

### Exercise

If you built the `customers` CRUD exercise in Module 06 as function-based
views, refactor it now into `CustomerListView`/`CustomerDetailView`/
`CustomerCreateView`/`CustomerUpdateView`/`CustomerDeleteView`, following
the exact pattern above. If you skipped that exercise, build it directly
as CBVs this time — either way, you should end up with a `customers/views.py`
that mirrors `catalog/views.py`'s structure closely.

## 7. Checkpoint — you should now be able to:

- [ ] Explain what `.as_view()` does and why a class becomes a valid view.
- [ ] Map each of `ListView`/`DetailView`/`CreateView`/`UpdateView`/
      `DeleteView` to the FBV pattern it replaces.
- [ ] Override `get_queryset()` to filter/search a `ListView`.
- [ ] Override `get_context_data()` correctly (calling `super()` first).
- [ ] Explain why `CreateView`/`UpdateView` don't need `success_url` when
      `get_absolute_url()` exists on the model, and when you'd set one anyway.
- [ ] Explain the difference between `reverse` and `reverse_lazy` and when
      each is required.
- [ ] Have refactored (or built) a second model's CRUD as CBVs.

## 8. What's next

**Module 08 — Authentication, Authorization & Permissions** finally locks
this down: right now, *anyone* can create, edit, or delete any product with
no login at all. We add real user accounts, a custom `User` model, groups/
permissions, and role-based access (staff/manager/customer) — and every CBV
you just wrote gets a one-line `LoginRequiredMixin`/`PermissionRequiredMixin`
to enforce it.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 08.
