import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from catalog.models import Product

pytestmark = pytest.mark.django_db

# The smallest valid GIF that exists (1x1 transparent pixel) — enough for
# Pillow (which ImageField uses to validate uploads) to accept it as a
# real image without shipping an actual binary fixture file in the repo.
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04"
    b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def _tiny_image(name="product.gif"):
    return SimpleUploadedFile(name, TINY_GIF, content_type="image/gif")


def test_creating_a_product_with_an_image_saves_and_serves_it(client, sales_rep_user, category):
    client.force_login(sales_rep_user)

    response = client.post(
        reverse("catalog:product_create"),
        {
            "name": "Photographed Widget", "sku": "PW-001", "category": category.pk,
            "price": "9.99", "cost_price": "4.00",
            "quantity_in_stock": 5, "reorder_level": 1, "is_active": "on",
            "image": _tiny_image(),
        },
    )

    assert response.status_code == 302
    product = Product.objects.get(sku="PW-001")
    assert product.image.name.startswith("products/product")
    # The uploaded bytes are actually retrievable, not just a filename recorded.
    assert product.image.read() == TINY_GIF


def test_product_without_an_image_has_a_falsy_image_field(product):
    assert not product.image


def test_api_serializer_exposes_image_url(api_client, admin_user, product):
    product.image.save("api-product.gif", SimpleUploadedFile("api-product.gif", TINY_GIF), save=True)
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(f"/api/products/{product.pk}/")

    assert response.status_code == 200
    assert response.data["image"] is not None
    assert "api-product" in response.data["image"]


def test_oversized_image_is_rejected(client, sales_rep_user, category, monkeypatch):
    # Rather than uploading an actual multi-megabyte fixture file, shrink
    # the limit itself so our real (tiny) test image now exceeds it —
    # exercises the exact same validator with a file that's cheap to ship.
    monkeypatch.setattr("catalog.validators.MAX_IMAGE_SIZE_BYTES", 10)
    client.force_login(sales_rep_user)

    response = client.post(
        reverse("catalog:product_create"),
        {
            "name": "Too Big", "sku": "TB-001", "category": category.pk,
            "price": "9.99", "cost_price": "4.00",
            "quantity_in_stock": 5, "reorder_level": 1, "is_active": "on",
            "image": _tiny_image(),
        },
    )

    assert response.status_code == 200  # re-rendered with errors, not redirected
    assert b"too large" in response.content
    assert not Product.objects.filter(sku="TB-001").exists()
