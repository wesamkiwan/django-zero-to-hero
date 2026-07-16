import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ProductForm
from .models import Category, Product


def _filter_products(request, qs):
    """Shared by the product list page and the CSV export, so "export"
    always means exactly "the products this same URL's filters currently
    show" — one filtering rule, not two copies that can drift apart."""
    query = request.GET.get("q", "").strip()
    if query:
        # Q lets you OR conditions together — a single filter() call only
        # ever ANDs its arguments, so matching "the search term anywhere
        # in name OR sku OR description" needs Q.
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(description__icontains=query)
        )

    category_id = request.GET.get("category", "").strip()
    if category_id:
        qs = qs.filter(category_id=category_id)

    stock = request.GET.get("stock", "").strip()
    if stock == "low":
        qs = qs.filter(quantity_in_stock__lte=F("reorder_level"))
    elif stock == "out":
        qs = qs.filter(quantity_in_stock=0)

    return qs


class ProductListView(ListView):
    model = Product
    context_object_name = "products"   # default would be "product_list" — kept
    paginate_by = 12                    # free pagination, no hand-written logic

    def get_queryset(self):
        qs = Product.objects.select_related("category", "supplier").filter(is_active=True)
        return _filter_products(self.request, qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["categories"] = Category.objects.all()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["selected_stock"] = self.request.GET.get("stock", "").strip()
        return context


def product_export_csv(request):
    """Exports exactly what the product list currently shows — same
    search/category/stock filters, no pagination limit — as a CSV file.
    A real-world staple: "give me this filtered view as a spreadsheet."
    """
    qs = _filter_products(
        request, Product.objects.select_related("category", "supplier").filter(is_active=True)
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(["SKU", "Name", "Category", "Price", "Quantity in stock", "Needs reorder"])
    for product in qs:
        writer.writerow([
            product.sku, product.name, product.category.name,
            product.price, product.quantity_in_stock, product.needs_reorder(),
        ])
    return response


class ProductDetailView(DetailView):
    model = Product
    # context_object_name not needed: DetailView already provides both
    # "object" and "product" (the model name, lowercased) by default —
    # which is exactly what product_detail.html already expects.


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.add_product"
    # success_url not set: CreateView falls back to self.object.get_absolute_url()
    # automatically — the exact same redirect target the FBV version used.

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'"{self.object.name}" was created.')
        return response


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.change_product"
    # Same story: no success_url needed, get_absolute_url() covers it.

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'"{self.object.name}" was updated.')
        return response


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    success_url = reverse_lazy("catalog:product_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'"{name}" was deleted.')
        return HttpResponseRedirect(success_url)
