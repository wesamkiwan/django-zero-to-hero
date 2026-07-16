# Module 04 — Models & the ORM

> **Where we're going:** Atlas gets a real, relational data model — products,
> categories, suppliers, customers, orders — and you'll understand exactly
> how a Python class becomes a database table, how relationships between
> tables work, and how to query them without writing SQL by hand.

## 1. What is an ORM, and why use one?

An **Object-Relational Mapper** lets you describe your data as Python
classes and work with rows as Python objects, while Django translates that
into SQL behind the scenes.

```python
# Instead of writing SQL like:
#   SELECT * FROM catalog_product WHERE price > 50 ORDER BY price DESC;
# you write:
Product.objects.filter(price__gt=50).order_by("-price")
```

Why this matters in practice:
- **Safety**: the ORM parameterizes queries for you, which is your default
  defense against SQL injection (Module 15 covers this explicitly).
- **Portability**: the same code runs against SQLite (development) or
  PostgreSQL (production, Module 16) with zero changes.
- **Productivity**: relationships, migrations, and validation are handled
  for you instead of hand-written in SQL and app code separately.

You *can* still drop to raw SQL when you truly need to (Module 12) — the ORM
doesn't take that away, it's just rarely necessary.

## 2. Defining a model

Every model is a Python class inheriting from `models.Model`; every class
attribute that's a `models.SomeField()` becomes a database column.

```python
# catalog/models.py
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Common field types you'll use constantly (all real, from Atlas's actual
models — open `project/atlas/catalog/models.py`, `customers/models.py`, and
`orders/models.py` alongside this section):

| Field | Stores | Notes |
|---|---|---|
| `CharField(max_length=...)` | short text | `max_length` is required |
| `TextField()` | long text | no length limit |
| `SlugField()` | URL-safe text | `office-supplies`, letters/numbers/hyphens |
| `EmailField()` | text | adds email format validation |
| `IntegerField()` / `PositiveIntegerField()` | whole numbers | |
| `DecimalField(max_digits=, decimal_places=)` | exact decimals | **always use for money**, never `FloatField` (binary floats lose precision) |
| `BooleanField(default=...)` | True/False | |
| `DateTimeField(auto_now_add=True)` | timestamp | set once, at creation |
| `DateTimeField(auto_now=True)` | timestamp | updated every save |
| `ForeignKey(...)` | a relationship | see §4 |
| `ManyToManyField(...)` | a relationship | see §4 |

Common field **options**, used on almost every field:
- `null=True` — allow `NULL` in the database (for non-string fields).
- `blank=True` — allow the field to be empty **in forms/validation** (a
  separate concern from `null`! `blank` is about forms, `null` is about the
  database — this trips everyone up at least once).
- `default=...` — a default value if none is given.
- `unique=True` — no two rows may share this value.
- `choices=...` — restrict to a fixed set of options (see `Order.Status` in
  `orders/models.py` for the modern `TextChoices` pattern).

## 3. Migrations — how your models become database tables

Django never touches your database directly when you edit `models.py`.
Instead, a two-step process:

```bash
python manage.py makemigrations   # 1. look at models.py, write a migration
                                    #    FILE describing what changed
python manage.py migrate          # 2. actually apply migration files
                                    #    to the database
```

A migration is a plain Python file describing one change (create a table,
add a column, ...). This gives you:
- A **history** of every schema change, in order, in version control.
- The ability to **replicate** the exact same schema on any machine/environment.
- A path to **roll back** if a migration turns out to be wrong.

**Never edit the database by hand once you're using migrations** — every
schema change goes through `makemigrations`. When we created `catalog`,
`customers`, and `orders`, running `makemigrations` produced:

```
Migrations for 'catalog':
  catalog\migrations\0001_initial.py
    + Create model Category
    + Create model Supplier
    + Create model Tag
    + Create model Product
Migrations for 'customers':
  customers\migrations\0001_initial.py
    + Create model Customer
Migrations for 'orders':
  orders\migrations\0001_initial.py
    + Create model Order
    + Create model OrderItem
```

Open one of those generated files in `project/atlas/*/migrations/0001_initial.py`
— it's readable Python, not magic.

## 4. Relationships — how tables connect

Three kinds, all used somewhere in Atlas or the demo:

### ForeignKey (many-to-one)

"Many of these belong to one of those." Atlas: many `Product`s belong to one
`Category`; many `OrderItem`s belong to one `Order`.

```python
category = models.ForeignKey(
    Category, on_delete=models.PROTECT, related_name="products"
)
```

- `on_delete` is **required**, no sane default exists — it says what happens
  to this row if the thing it points to is deleted:
  - `CASCADE` — delete this row too (Atlas: deleting an `Order` deletes its `OrderItem`s — they're meaningless without it).
  - `PROTECT` — refuse to delete the parent while this exists (Atlas: you
    can't delete a `Category` that still has `Product`s, or a `Customer`
    with existing `Order`s — protects against silently orphaning business data).
  - `SET_NULL` — set this FK to `NULL` instead (requires `null=True`; Atlas:
    deleting a `Supplier` just detaches its `Product`s rather than destroying them).
- `related_name` — lets you query **backwards**: `some_category.products.all()`
  gets every `Product` in that category. Always set this explicitly and
  give it a sensible plural name — the default (`product_set`) is workable
  but far less readable.

### ManyToManyField

"Many of these relate to many of those, and vice versa." Atlas:
a `Product` can have several `Tag`s, and a `Tag` can apply to many `Product`s.

```python
tags = models.ManyToManyField(Tag, blank=True, related_name="products")
```

Django manages a hidden join table for you. Only one side declares the
field; both sides get a manager: `product.tags.add(tag)`,
`product.tags.set([tag1, tag2])`, `tag.products.all()`.

### OneToOneField

"Exactly one of these relates to exactly one of those." Atlas's real schema
doesn't need one, so we isolated this in a dedicated demo instead of forcing
an artificial one into the business schema. Go run
`demo/relationships_playground/` now and follow its `README.md` — it's a
classic Author/Book/Genre/AuthorProfile example with a **real, verified**
shell transcript proving FK, O2O, and M2M all work exactly as described,
including the database rejecting a duplicate one-to-one row.

## 5. QuerySets — how you actually fetch data

`Model.objects` is a **manager** — your entry point to querying that table.
Everything it returns is a **QuerySet**, which is **lazy**: building one
doesn't hit the database — only iterating it, calling `list()` on it,
printing it, etc. does. This lets you build up a query across multiple
lines/conditions before it actually runs.

```python
Product.objects.all()                          # every row
Product.objects.filter(price__gt=50)            # WHERE price > 50
Product.objects.exclude(supplier=None)           # WHERE supplier IS NOT NULL
Product.objects.get(sku="KB-001")               # exactly one row, or raises
                                                  # DoesNotExist / MultipleObjectsReturned
Product.objects.order_by("-price")              # ORDER BY price DESC
Product.objects.values("name", "price")         # dicts instead of model instances
Category.objects.get_or_create(name="Office Supplies", defaults={"slug": "office-supplies"})
```

Common **field lookups** (the `__gt` part above) — these go after a double
underscore on the field name:

| Lookup | Meaning |
|---|---|
| `field__gt`, `__gte`, `__lt`, `__lte` | greater/less than (or equal) |
| `field__contains`, `__icontains` | substring match (case-insensitive with `i`) |
| `field__in=[...]` | value is one of a list |
| `field__isnull=True` | IS NULL |
| `related__field` | traverse a relationship, e.g. `product__category__name` |

## 6. Model methods and properties

Beyond fields, a model is a normal Python class — add whatever helper logic
belongs with the data:

```python
# catalog/models.py — Product
def __str__(self):
    return f"{self.name} ({self.sku})"          # what shows in admin/shell/etc.

@property
def in_stock(self):
    return self.quantity_in_stock > 0            # product.in_stock, no ()

def needs_reorder(self):
    return self.quantity_in_stock <= self.reorder_level
```

`__str__` is worth special mention: **always define it**. Without it,
every object prints as `Product object (1)` everywhere — the admin, the
shell, error messages — which is nearly useless for debugging.

## 7. The `manage.py shell` — your ORM playground

```bash
python manage.py shell
```

Opens a normal Python REPL with all your models already importable and
Django fully configured — the fastest way to experiment with queries before
writing them into a view.

## 8. Atlas's real data model, explained

Open these three files now, side by side with this lesson:
`project/atlas/catalog/models.py`, `project/atlas/customers/models.py`,
`project/atlas/orders/models.py`.

```
Category ──┬─< Product >──< Tag        (FK + M2M)
Supplier ──┘        \
                      >─────┐
Customer ──< Order ──< OrderItem       (FK chains across three apps)
```

- `catalog` app: `Category`, `Supplier`, `Tag`, `Product` — the inventory side.
- `customers` app: `Customer` — the CRM side.
- `orders` app: `Order`, `OrderItem` — ties the two together. Note
  `orders/models.py` imports models from **both** other apps — this is
  completely normal; apps aren't isolated silos, they're organizational
  units, and cross-app foreign keys are how real Django projects connect
  business domains.
- `OrderItem.unit_price` **snapshots** the price at order time, deliberately
  separate from `Product.price` — if a product's price changes later, past
  orders must still reflect what the customer actually paid. This is a real
  business rule, not an ORM quirk — notice how modeling it is just "add
  another field," nothing exotic.
- `Order.total` and `Product.in_stock`/`needs_reorder()` are computed from
  other fields rather than stored — this is a deliberate choice (a stored
  "cached total" could drift out of sync if items change; Module 12 revisits
  this trade-off when we discuss performance).

## 9. Hands-on: build real data, see it flow through to the page

In `project/atlas/`, with your venv active:

```bash
python manage.py migrate
python manage.py shell
```

Then paste this in (or type it — better retention):

```python
from catalog.models import Category, Supplier, Tag, Product
from customers.models import Customer
from orders.models import Order, OrderItem

electronics = Category.objects.create(name="Electronics", slug="electronics")
techdistro = Supplier.objects.create(name="TechDistro Inc", email="sales@techdistro.example")
bestseller = Tag.objects.create(name="bestseller")

keyboard = Product.objects.create(
    name="Mechanical Keyboard", sku="KB-001", category=electronics, supplier=techdistro,
    price="79.99", cost_price="40.00", quantity_in_stock=12, reorder_level=5,
)
keyboard.tags.add(bestseller)

mouse = Product.objects.create(
    name="Wireless Mouse", sku="MS-001", category=electronics, supplier=techdistro,
    price="29.99", cost_price="12.00", quantity_in_stock=3, reorder_level=5,
)

monitor = Product.objects.create(
    name='27" Monitor', sku="MN-001", category=electronics, supplier=techdistro,
    price="249.00", cost_price="150.00", quantity_in_stock=0, reorder_level=5,
)

customer = Customer.objects.create(first_name="Jane", last_name="Doe", email="jane@example.com")
order = Order.objects.create(customer=customer)
OrderItem.objects.create(order=order, product=keyboard, quantity=2, unit_price=keyboard.price)
OrderItem.objects.create(order=order, product=mouse, quantity=1, unit_price=mouse.price)

print(order.total)                # 189.97 — computed from OrderItems
print(list(customer.orders.all()))  # reverse FK
print([p.name for p in Product.objects.all() if p.needs_reorder()])
```

This is exactly what we ran to verify Atlas's models — real output, not
hypothetical. Then exit the shell (`exit()`) and run the server:

```bash
python manage.py runserver
```

Visit `/products/` — it's the same template from Module 03, but
`pages/views.py` now queries `Product.objects.filter(is_active=True)`
instead of a hardcoded list. Compare `pages/views.py` to its Module 03
version (check `git log` / `git diff` if you want to see it precisely) —
the template needed **zero changes** for this.

### Exercise

Using the shell, add a second `Order` for a new `Customer`, containing at
least two `OrderItem`s referencing products that already exist. Then:
1. Query all orders for that customer (`customer.orders.all()`).
2. Compute and print that order's `.total`.
3. Use `Product.objects.filter(quantity_in_stock__lt=5)` to find low-stock
   products and cross-check the result against `needs_reorder()`.

## 10. Checkpoint — you should now be able to:

- [ ] Explain what an ORM does and why `DecimalField` beats `FloatField` for money.
- [ ] Write a model with at least four different field types and two options
      (`null`, `blank`, `default`, `unique`, or `choices`).
- [ ] Explain the two-step migration process and why you never hand-edit the
      database schema once using migrations.
- [ ] Choose the correct `on_delete` behavior (`CASCADE`/`PROTECT`/`SET_NULL`)
      for a given relationship and justify it in terms of the business rule.
- [ ] Explain the difference between `ForeignKey`, `ManyToManyField`, and
      `OneToOneField`, with a real example of each.
- [ ] Write a QuerySet using `filter`, `exclude`, `order_by`, and at least
      two field lookups (`__gt`, `__icontains`, etc.).
- [ ] Explain why QuerySets are "lazy" and why that matters.
- [ ] Have completed the exercise above in a real shell session.

## 11. What's next

**Module 05 — Django Admin Mastery** takes these exact models and gives you
a full, customized, production-quality admin interface for managing them —
list filters, search, inlines for `OrderItem` inside `Order`, and more —
usually in under an hour of work, which is one of Django's most famous
productivity wins.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 05.
