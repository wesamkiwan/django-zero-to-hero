from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Product


def product_list(request):
    products = Product.objects.filter(is_active=True)

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(name__icontains=query)

    context = {"products": products, "query": query}
    return render(request, "catalog/product_list.html", context)


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


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" was updated.')
            return redirect("catalog:product_detail", pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, "catalog/product_form.html", {"form": form, "is_create": False, "product": product})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" was deleted.')
        return redirect("catalog:product_list")

    return render(request, "catalog/product_confirm_delete.html", {"product": product})
