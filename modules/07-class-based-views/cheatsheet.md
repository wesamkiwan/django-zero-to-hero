# Cheat Sheet — Module 07: Class-Based Views & Generic Views

## URL wiring

```python
path('', views.ProductListView.as_view(), name='product_list'),
```

## The five generic views

```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

class ProductListView(ListView):
    model = Product
    context_object_name = "products"     # default: "product_list"/"object_list"
    paginate_by = 12                      # free pagination

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        return qs.filter(name__icontains=q) if q else qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)   # ALWAYS call super() first
        context["extra"] = "..."
        return context


class ProductDetailView(DetailView):
    model = Product
    # default context names: "object" AND "<model_name_lowercase>"


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    # success_url not needed if model.get_absolute_url() exists

    def form_valid(self, form):
        response = super().form_valid(form)   # does form.save() + builds redirect
        messages.success(self.request, "Created.")
        return response


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    # same form_valid() pattern as CreateView


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("catalog:product_list")   # required — no natural default

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "Deleted.")
        return HttpResponseRedirect(success_url)
```

## Default template names (convention over configuration)

| View | Default template |
|---|---|
| `ListView` | `<app>/<model>_list.html` |
| `DetailView` | `<app>/<model>_detail.html` |
| `CreateView` / `UpdateView` | `<app>/<model>_form.html` |
| `DeleteView` | `<app>/<model>_confirm_delete.html` |

## Default context variable names

| View | Provides |
|---|---|
| `ListView` | `object_list` (or `<model>_list`), override via `context_object_name` |
| `DetailView` / `UpdateView` | `object` and `<model_name>` |
| `CreateView` | `form` (no object until saved) |

## `reverse` vs `reverse_lazy`

- **Class body / class attribute** (evaluated at import time): use `reverse_lazy`.
- **Inside a method** (evaluated per-request, URLconf already loaded): `reverse` is fine.

## Pagination template snippet

```django
{% if is_paginated %}
    {% if page_obj.has_previous %}<a href="?page={{ page_obj.previous_page_number }}">Prev</a>{% endif %}
    Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
    {% if page_obj.has_next %}<a href="?page={{ page_obj.next_page_number }}">Next</a>{% endif %}
{% endif %}
```

## Decision rule

Use a generic CBV for standard "fetch object(s) / render or process a form"
CRUD. Use a plain function view when the logic doesn't map onto that shape
(webhooks, multi-purpose branching views, one-off redirects).
