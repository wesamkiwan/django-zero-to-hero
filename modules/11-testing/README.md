# Module 11 — Testing

> **Where we're going:** every scratch verification script we wrote by hand
> throughout Modules 04-10 (seed some data, hit a URL, check the response,
> throw the script away) becomes a **permanent, automated test suite** —
> 34 tests covering models, views, permissions, and the API — that catches
> regressions the moment they happen, not whenever you next click around
> the app manually.

## 1. Why tests, beyond "it's good practice"

Every module so far, we verified behavior by writing a throwaway script,
running it once, reading the output, then deleting it. That worked, but:
it only ran **once**, by **us**, at **that moment**. The instant you change
`ProductForm.clean_price()` next month, nothing tells you if you broke the
"cost price can't exceed price" rule — unless you remember to re-verify by
hand. A test suite is exactly that verification, kept around permanently
and re-run automatically.

## 2. pytest-django, factory_boy — the professional toolkit

```bash
pip install pytest pytest-django factory-boy coverage
```

- **pytest** — the test runner (Django's own `manage.py test` works too;
  `pytest` is the more widely used tool in real projects for its nicer
  syntax and plugin ecosystem).
- **pytest-django** — teaches pytest about Django (test database setup,
  the `db` fixture, `client`, settings loading).
- **factory_boy** — generates realistic test data without repeating
  `Model.objects.create(field1=..., field2=..., ...)` in every single test.
- **coverage** — measures what percentage of your code the test suite
  actually exercises.

Configuration lives in two small files at the project root:

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
addopts = --reuse-db
```

`--reuse-db` keeps the test database between runs instead of rebuilding it
every time (much faster locally; CI typically drops this flag to always
start clean).

## 3. Factories — realistic data, one line per test

```python
# catalog/factories.py
class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    sku = factory.Sequence(lambda n: f"SKU-{n:04d}")
    category = factory.SubFactory(CategoryFactory)
    price = Decimal("19.99")
    ...
```

`factory.Sequence` guarantees uniqueness across however many you create in
one test run (`Product 0`, `Product 1`, ...) — essential since `sku` is
`unique=True`. `factory.SubFactory` auto-creates a related object
(`Category`) if you don't supply one, but still accepts an override:
`ProductFactory(category=my_category)`.

Then in tests: `product = ProductFactory()` gives you a fully valid,
saved `Product` in one line, instead of six lines of `Model.objects.create(...)`.

## 4. A real bug our own test suite caught immediately

Writing `orders/tests/test_models.py`, this test:

```python
def test_order_item_line_total():
    item = OrderItemFactory(quantity=3, unit_price="10.00")
    assert item.line_total == Decimal("30.00")
```

**failed**, with `'10.0010.0010.00' == Decimal('30.00')` — Python happily
computed `"10.00" * 3` as **string repetition**, not multiplication,
because `unit_price` was still a plain `str` in memory, not a `Decimal`.

Why: Django only converts a `DecimalField`'s input to a real `Decimal`
when it goes through a **Form or Serializer's validation** — every
HTTP-level view/API test we'd run so far worked correctly precisely
*because* the data flowed through `ProductForm`/`ProductSerializer` first.
A factory (or any direct `Model.objects.create(unit_price="10.00")` call)
bypasses that entirely — the field holds whatever raw value you gave it
until the instance is reloaded from the database.

A sibling test hit the same root cause with a clearer symptom —
`Product.profit_margin` raised `TypeError: unsupported operand type(s) for
-: 'str' and 'str'` outright, because subtracting two strings isn't
silently wrong, it's a hard error. **The string-repetition version is the
more dangerous one**: it's not an error, it's a wrong number that looks
plausible.

**The fix**: factories should hand out the same *types* real code paths
produce — `Decimal("19.99")`, not `"19.99"`:

```python
price = Decimal("19.99")   # not "19.99"
```

This is exactly the kind of bug a test suite exists to catch — and,
worth noting honestly, it's a bug **in the test data setup**, not in
`Product.profit_margin` or `OrderItem.line_total` themselves (both work
correctly whenever real Decimal values reach them, which is always true
via the actual forms/serializers). Still: if our factories can trigger it,
so can any other code path that assigns a raw string directly — the fix
makes the test suite's data match production's, not just paper over a
one-off assertion.

## 5. The test suite itself

```
accounts/tests/test_auth.py     — signup, login, logout, default role
catalog/tests/test_models.py    — Product/Category properties & M2M
catalog/tests/test_views.py     — list/search/404, permission gating, validation
catalog/tests/test_api.py       — same, via the REST API
customers/tests/test_models.py  — full_name property
orders/tests/test_models.py     — Order.total, OrderItem.line_total
orders/tests/test_api.py        — writable nested serializer create/update
```

A representative view test — this is Module 08's permission verification,
now permanent:

```python
def test_logged_in_customer_without_permission_gets_403(client, customer_user):
    client.force_login(customer_user)
    response = client.get(reverse("catalog:product_create"))
    assert response.status_code == 403


def test_sales_rep_can_create_product(client, sales_rep_user, category, supplier):
    client.force_login(sales_rep_user)
    response = client.post(reverse("catalog:product_create"), {...})
    assert response.status_code == 302
    assert Product.objects.filter(sku="NP-001").exists()
```

`client.force_login(user)` logs a user in directly, skipping the actual
login form — the right tool when the login flow itself isn't what you're
testing (that's `accounts/tests/test_auth.py`'s job instead).

`conftest.py` holds shared **fixtures** (`category`, `product`, `customer`,
`customer_user`, `sales_rep_user`, `admin_user`, `api_client`) — pytest
automatically injects a fixture into any test function that names it as a
parameter, no imports needed inside the test file itself.

## 6. Running the suite, and measuring coverage

```bash
pytest                          # run everything
pytest catalog/                 # just one app
pytest -k "permission"          # tests whose name contains "permission"
pytest -v                       # verbose: one line per test

coverage run -m pytest
coverage report                 # per-file % of lines actually executed
coverage html                   # generates htmlcov/index.html, browsable
```

Our own run: **34 tests, all passing, 93% coverage** across the project
(`.coveragerc` excludes migrations, `factories.py`, and the test files
themselves from the denominator — those aren't "your logic" to cover).
100% is not the goal — it's a signal to look at *what's* uncovered
(`catalog/views.py` at 79%, `pages/views.py` at 76%) and decide if that
gap is a real gap (untested error path) or noise (an admin `__str__` never
hit by these particular tests).

## 7. The TDD mindset, briefly

Test-Driven Development means writing the failing test **first**, then
the code that makes it pass. We didn't do that historically in this
course (we built features, then verified) — but going forward, for any
non-trivial new rule (a validation constraint, a permission boundary), try
writing the test first once: it forces you to state precisely what
"correct" means *before* you're biased by whatever you're about to
implement, and you get an immediate, unambiguous signal the moment it
passes.

## 8. Hands-on

```bash
cd project/atlas
pip install -r requirements-dev.txt
pytest -v
coverage run -m pytest
coverage report
```

### Exercise

Write tests for the `customers` CRUD views (if you built them in Module
06/07's exercise) or for the Manager group (Module 08's exercise),
following the exact patterns in `catalog/tests/test_views.py`:
anonymous-blocked, unprivileged-403, privileged-succeeds, plus one
validation-rejection test.

## 9. Checkpoint — you should now be able to:

- [ ] Explain what pytest-django and factory_boy each add on top of
      Django's own testing tools.
- [ ] Write a factory with `Sequence` and `SubFactory`.
- [ ] Explain why a Decimal field can hold a plain string in memory, and
      when that stops being safe to use in arithmetic.
- [ ] Write tests covering: a model method, a permission boundary
      (anonymous/unprivileged/privileged), and a validation rule.
- [ ] Run `pytest` and `coverage report`, and interpret what an
      uncovered line is telling you.
- [ ] Have completed the exercise above.

## 10. What's next

**Module 12 — Advanced ORM, Query Optimization & Caching** goes back into
the models we now have a safety net for, and asks: how many actual SQL
queries does each page run, and how do we cut that down? `select_related`/
`prefetch_related` (already used a few times, informally), aggregation,
`F()` expressions properly, and caching.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 12.
