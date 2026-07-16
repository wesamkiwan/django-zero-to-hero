# Module 15 — Security Best Practices

> **Where we're going:** a critical pass over everything built so far.
> Django already defends against most of the OWASP Top 10 by default —
> this module is mostly about *not undoing that*, closing the gaps that
> are still on you (secrets, deploy settings, rate limits, upload size),
> and proving it with the exact command a real deployment checklist runs:
> `manage.py check --deploy`.

## 1. The OWASP Top 10, in a Django context

A quick survey of where Atlas already stands, module by module:

- **Injection (SQL)** — the ORM parameterizes every query it builds
  (`Product.objects.filter(name=user_input)` is always safe). The risk
  only shows up with hand-written raw SQL/`.extra()` string-formatted
  with user input — Atlas has none, and the rule going forward is simple:
  if you ever need raw SQL, use `cursor.execute(sql, [params])`'s
  parameter substitution, never an f-string.
- **Broken authentication** — Module 08's custom `User` model, Django's
  battle-tested password hashing, and (new this module) API rate
  limiting on login/every endpoint (§4 below).
- **Cross-Site Scripting (XSS)** — Django templates auto-escape every
  variable by default (`{{ product.name }}` is always safe even if a
  product's name contained `<script>`). The only way to reintroduce XSS
  is `|safe` or `mark_safe()` — reach for `format_html()` instead, which
  Module 14's admin customizations already did correctly for exactly this
  reason (`image_preview`, `invoice_link` — both build HTML with
  variables, safely).
- **Cross-Site Request Forgery (CSRF)** — `CsrfViewMiddleware` plus every
  `{% csrf_token %}` in Atlas's forms, since Module 06.
- **Security misconfiguration** — the entire subject of §2 and §3 below;
  this is where a course project and a real deployment differ most.
- **Sensitive data exposure** — secrets management, §3.
- **Broken access control** — Module 08's permission system, Module 14's
  ownership checks (404, not 403, for someone else's notification).

The pattern across all of these: Django's defaults are already good.
Security work here is mostly **configuration and vigilance**, not writing
novel defenses from scratch.

## 2. `manage.py check --deploy` — a real, running safety net

Before changing anything, here's what Atlas's settings actually produce
today:

```
$ python manage.py check --deploy
System check identified some issues:

WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting...
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True...
?: (security.W009) Your SECRET_KEY has less than 50 characters... or it's prefixed with 'django-insecure-'...
?: (security.W012) SESSION_COOKIE_SECURE is not set to True...
?: (security.W016) ... you have not set CSRF_COOKIE_SECURE to True...
?: (security.W018) You should not have DEBUG set to True in deployment.
?: (security.W020) ALLOWED_HOSTS must not be empty in deployment.

System check identified 7 issues (0 silenced).
```

Seven real, specific, actionable findings — not hypothetical advice.
`--deploy` runs a set of checks that are **off by default** (they'd be
noise during development) and on only when you explicitly ask, right
before shipping. This module fixes every one of them.

## 3. Secrets and settings, properly

```python
# config/settings.py
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")   # no-op if the file doesn't exist

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-...")   # fallback keeps runserver working with zero setup
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

`.env` (gitignored) holds real values; `.env.example` (committed)
documents every variable with a safe placeholder, so cloning the repo
still works with zero setup, and setting up a real deployment means
copying one file and filling in real answers — not reverse-engineering
which env vars `settings.py` reads.

The `if not DEBUG:` block only makes sense for a site actually served
over HTTPS — true of any real deployment, never true of plain local
`runserver`, which is why it's gated on `DEBUG` rather than applied
unconditionally (that would break `http://127.0.0.1:8000` immediately:
`SECURE_SSL_REDIRECT = True` unconditionally would redirect-loop a
plain-HTTP dev server forever).

**Verifying the fix, not just believing it:**

```
$ SECRET_KEY="a-properly-random-fifty-character-value..." DEBUG=False ALLOWED_HOSTS="atlas.example" python manage.py check --deploy
System check identified no issues (0 silenced).
```

All 7 warnings gone, with real, non-default values — proof this actually
works, not just settings that "look" secure.

### A subtlety this surfaced — and a callback to Module 13

Testing this in pytest is trickier than it looks:

```python
def test_check_deploy_passes_when_production_settings_are_set(settings):
    settings.DEBUG = False
    settings.SECRET_KEY = "a-properly-random-key-..."
    settings.ALLOWED_HOSTS = ["atlas.example"]
    settings.SECURE_SSL_REDIRECT = True
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    settings.SECURE_HSTS_SECONDS = 31536000
    settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    settings.SECURE_HSTS_PRELOAD = True
    ...
```

Every relevant setting is overridden **individually** here — just flipping
`settings.DEBUG = False` and expecting the `if not DEBUG:` block in
`settings.py` to "notice" and set the rest doesn't work, for the exact
reason Module 13's Celery bug taught: that conditional block already ran
**once**, at process startup, using whatever `DEBUG` the environment
actually had at that moment (`True`, since no `.env` sets it in this
course). A later override of `settings.DEBUG` inside a test doesn't
rewind and re-execute code that already ran. Settings modules aren't
"live" — they're a script that runs once.

## 4. Rate limiting the API

```python
# settings.py
REST_FRAMEWORK = {
    ...
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/minute", "user": "100/minute"},
}
```

Two separate rates, not one: an anonymous caller (hasn't proven who they
are) gets a much lower ceiling than an authenticated one — otherwise
there's nothing stopping a script from hammering `/api/token/` trying
passwords, or scraping the entire catalog in a tight loop.

```python
def test_anonymous_requests_are_throttled_past_the_configured_rate(api_client):
    cache.clear()   # LocMemCache persists for the whole test process, not per-test
    responses = [api_client.get("/api/products/") for _ in range(ANON_RATE + 1)]
    assert all(r.status_code == 200 for r in responses[:ANON_RATE])
    assert responses[ANON_RATE].status_code == 429
```

**Another import-time caching gotcha, same family as Module 13's:** the
first version of this test tried overriding
`settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` per-test to a small
number, for speed. It passed alone and failed inside the full suite —
because DRF's throttle classes read `DEFAULT_THROTTLE_RATES` into a
**class attribute**, once, the first time `rest_framework.throttling` is
imported (`THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES` at class
body execution). Whichever test in the suite happens to import that
module *first* locks in whatever rate was configured **at that moment**
— a later test's settings override changes the Django setting, but not
the already-bound class attribute reading from it. The fix: test against
the real, permanent rate from `settings.py` instead of trying to shrink
it per-test. The generalizable lesson, worth carrying past this one
library: **before you override a setting inside a test to make it
faster/smaller, check whether anything reads that setting once at import
or class-definition time** — if it does, your override arrives too late
for anything that already ran.

## 5. Upload size limits

Module 14 added `Product.image`, validated (via Pillow) to really be an
image — but nothing stopped a 2 GB "image" from being uploaded:

```python
# catalog/validators.py
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_image_size(image_file):
    if image_file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(f"Image file too large ({image_file.size / 1024 / 1024:.1f} MB). "
                               f"Maximum size is {MAX_IMAGE_SIZE_BYTES / 1024 / 1024:.0f} MB.")
```

```python
# catalog/models.py
image = models.ImageField(upload_to="products/", blank=True, null=True, validators=[validate_image_size])
```

Without a size limit, "upload a product photo" — a feature already
gated behind login and a real permission — is still a denial-of-service
vector: repeated large uploads can fill disk or exhaust request-handling
workers on nothing but I/O, before any application logic even runs. This
is exactly the kind of gap a feature module (14) doesn't always catch,
because it was busy proving the feature *works*; a security pass (15)
comes back specifically asking "how could this be abused?"

```python
def test_oversized_image_is_rejected(client, sales_rep_user, category, monkeypatch):
    monkeypatch.setattr("catalog.validators.MAX_IMAGE_SIZE_BYTES", 10)   # shrink the limit, not the fixture
    ...
    assert b"too large" in response.content
    assert not Product.objects.filter(sku="TB-001").exists()
```

Shrinking the limit (via `monkeypatch`, auto-reverted after the test)
rather than uploading an actual multi-megabyte file keeps the test fast
and the repo free of a large binary fixture, while still exercising the
real validator against a real (tiny) upload.

## 6. Hands-on

```bash
cd project/atlas
cp .env.example .env   # then fill in real values for a production-like run
pip install -r requirements-dev.txt
python manage.py check --deploy          # see the 7 warnings for yourself
# now edit .env: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS
python manage.py check --deploy          # 0 issues
```

### Exercise

Add throttling specifically to `POST /api/token/` (obtaining an auth
token) at a much lower rate than the general API — 5/minute, say — since
that's the one endpoint an attacker would actually want to hammer
(password guessing). DRF's `ScopedRateThrottle` (a `throttle_scope`
attribute per view, plus a `"scopes"` key in `DEFAULT_THROTTLE_RATES`) is
built for exactly this "one endpoint needs its own rate" case — look up
its docs and wire it in, then write a test proving the general API rate
(20/minute) and the token endpoint's rate are enforced independently.

## 7. Checkpoint — you should now be able to:

- [ ] Map each OWASP Top 10 category to where Django defends against it
      by default, and where that protection is still on you.
- [ ] Run `manage.py check --deploy` and read its output.
- [ ] Load secrets from a `.env` file via `python-dotenv`, with an
      `.env.example` documenting every variable.
- [ ] Explain why `SECURE_SSL_REDIRECT` and friends must be conditional
      on `DEBUG`, not unconditional.
- [ ] Explain why testing "settings resolved by a conditional block" means
      overriding every resulting setting individually, not just the
      condition — and why (a callback to Module 13's lesson).
- [ ] Configure DRF throttling with separate anon/user rates, and know to
      check whether a setting you're overriding in a test was already
      cached elsewhere at import time.
- [ ] Add a file-size validator to an upload field and explain the
      denial-of-service risk it closes.
- [ ] Have completed (or at least researched) the `ScopedRateThrottle` exercise above.

## 8. What's next

**Module 16 — Configuration, Docker & Deployment** takes everything this
module set up (env-based settings, `.env`) and actually deploys Atlas:
Docker & docker-compose, a real PostgreSQL database instead of SQLite,
Gunicorn/Nginx, and CI/CD with GitHub Actions.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 16.
