# Cheat Sheet — Module 11: Testing

## Setup

```bash
pip install pytest pytest-django factory-boy coverage
```
```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
addopts = --reuse-db
```
```ini
# .coveragerc
[run]
omit = */migrations/*, manage.py, */tests/*, conftest.py, */factories.py
```

## Factory

```python
class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")   # unique per call
    category = factory.SubFactory(CategoryFactory)        # auto-creates related obj
    price = Decimal("19.99")                              # Decimal, NOT a plain string!
```

**Gotcha**: Django only coerces a `DecimalField` input to `Decimal` when it
passes through a Form/Serializer's validation. A factory (or any direct
`Model.objects.create(...)`) that hands it a raw string leaves it a `str`
in memory — arithmetic on it either errors (`str - str`) or silently gives
the wrong answer (`"10.00" * 3 == "10.0010.0010.00"`, string repetition).
Always pass `Decimal(...)` in factories/tests for decimal fields.

## Custom post_generation hook (future-proof over PostGenerationMethodCall)

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")
        if create:
            self.save()
```

## conftest.py fixtures

```python
@pytest.fixture
def product(category, supplier):
    return ProductFactory(category=category, supplier=supplier)

@pytest.fixture
def sales_rep_user(sales_team_group):
    user = UserFactory()
    user.groups.add(sales_team_group)
    return user

@pytest.fixture
def api_client():
    return APIClient()
```
Any test function that names a fixture as a parameter gets it injected
automatically — no imports needed.

## Writing tests

```python
pytestmark = pytest.mark.django_db   # module-level: every test gets DB access

def test_something(client, product):             # Django test client
    response = client.get(reverse("catalog:product_list"))
    assert response.status_code == 200

def test_permission(client, customer_user):
    client.force_login(customer_user)             # skip the actual login form
    response = client.get(reverse("catalog:product_create"))
    assert response.status_code == 403

def test_api(api_client, sales_rep_user):          # DRF's APIClient
    api_client.force_authenticate(user=sales_rep_user)
    response = api_client.post("/api/products/", {...}, format="json")
    assert response.status_code == 201
```

## Running

```bash
pytest                    # everything
pytest catalog/           # one app
pytest -k "permission"    # name matches
pytest -v                 # verbose

coverage run -m pytest
coverage report
coverage html              # htmlcov/index.html
```

## TDD in one sentence

For a new rule (validation, permission boundary): write the failing test
first — it forces you to state "correct" precisely before you're biased
by the implementation you're about to write.
