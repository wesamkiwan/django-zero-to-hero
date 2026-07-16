# Cheat Sheet — Module 04: Models & the ORM

## Migration commands

```bash
python manage.py makemigrations [app_label]   # generate migration file(s)
python manage.py migrate                      # apply them
python manage.py sqlmigrate app_label 0001    # see the actual SQL a migration runs
python manage.py showmigrations               # see applied/unapplied migrations
```

## Common field types

```python
models.CharField(max_length=100)
models.TextField()
models.SlugField()
models.EmailField()
models.IntegerField() / models.PositiveIntegerField()
models.DecimalField(max_digits=10, decimal_places=2)   # use for money, never FloatField
models.BooleanField(default=True)
models.DateTimeField(auto_now_add=True)   # set once, at creation
models.DateTimeField(auto_now=True)       # updated on every save
```

Common options: `null=True` (DB-level), `blank=True` (form-level),
`default=`, `unique=True`, `choices=`.

## Choices (modern pattern)

```python
class Status(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"

status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
# order.get_status_display() -> human-readable label
```

## Relationships

```python
# Many-to-one
category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

# Many-to-many
tags = models.ManyToManyField(Tag, blank=True, related_name="products")

# One-to-one
profile = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="profile")
```

`on_delete` choices: `CASCADE` (delete children too), `PROTECT` (block
deletion while children exist), `SET_NULL` (needs `null=True`),
`SET_DEFAULT`, `DO_NOTHING` (rarely safe).

Traversal:
```python
category.products.all()   # reverse FK, via related_name
product.tags.all()        # forward M2M
tag.products.all()        # reverse M2M, via related_name
author.profile            # forward O2O
profile.author            # reverse O2O
```

## QuerySets

```python
Model.objects.all()
Model.objects.filter(field=value)
Model.objects.exclude(field=value)
Model.objects.get(field=value)              # exactly one, or raises
Model.objects.order_by("field", "-other")   # "-" = descending
Model.objects.values("field1", "field2")    # dicts, not instances
Model.objects.get_or_create(field=value, defaults={...})
```

Field lookups: `__gt` `__gte` `__lt` `__lte` `__contains` `__icontains`
`__in` `__isnull` — and traverse relations with `__`: `product__category__name`.

QuerySets are **lazy** — building one issues no query; iterating,
`list()`-ing, or printing it does.

## Model methods worth always writing

```python
def __str__(self):
    return self.name          # readable everywhere: admin, shell, errors

def get_absolute_url(self):
    return reverse("app:detail", args=[self.pk])

@property
def computed_thing(self):
    return self.a + self.b    # accessed WITHOUT parens: obj.computed_thing
```

## Meta options

```python
class Meta:
    ordering = ["name"]
    verbose_name_plural = "categories"
    indexes = [models.Index(fields=["sku"])]
    constraints = [models.UniqueConstraint(fields=["order", "product"], name="...")]
```

## Shell

```bash
python manage.py shell
```
