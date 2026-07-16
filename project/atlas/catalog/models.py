from django.db import models
from django.db.models import F
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Free-form labels a product can carry, e.g. 'bestseller', 'clearance'.
    A Product can have many Tags, and a Tag can apply to many Products —
    a many-to-many relationship."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField("SKU", max_length=32, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            # Speeds up exactly the query the dashboard/low_stock_count
            # tag runs constantly: active products at or below reorder
            # level. A composite index matching your actual filter
            # columns helps far more than indexing each column separately.
            models.Index(fields=["is_active", "quantity_in_stock"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        # This URL name doesn't exist until Module 06/07 add catalog views.
        # Defining get_absolute_url() now is standard practice — it's the
        # one place a model says "here's my canonical page" once that page
        # exists, and templates/redirects can call it without hardcoding paths.
        return reverse("catalog:product_detail", args=[self.pk])

    @property
    def in_stock(self):
        return self.quantity_in_stock > 0

    @property
    def profit_margin(self):
        if self.price == 0:
            return 0
        return (self.price - self.cost_price) / self.price * 100

    def needs_reorder(self):
        return self.quantity_in_stock <= self.reorder_level

    def adjust_stock(self, delta):
        """Change quantity_in_stock by delta (negative to reduce, positive
        to restock) ATOMICALLY at the database level, using F() instead of
        `self.quantity_in_stock += delta; self.save()`.

        The naive version reads the current value into Python, adds delta,
        then writes it back — if two requests do this concurrently, both
        read the same starting value and the second write clobbers the
        first (a "lost update"). F("quantity_in_stock") + delta becomes
        part of the SQL UPDATE statement itself
        (`UPDATE ... SET quantity_in_stock = quantity_in_stock + delta`),
        so the database applies both changes correctly regardless of
        which request's UPDATE runs first.
        """
        Product.objects.filter(pk=self.pk).update(
            quantity_in_stock=F("quantity_in_stock") + delta
        )
        self.refresh_from_db(fields=["quantity_in_stock"])
