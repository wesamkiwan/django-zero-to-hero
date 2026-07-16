# Cheat Sheet — Module 15: Security Best Practices

## OWASP Top 10 quick map (Django's default posture)

| Risk | Django's default defense |
|---|---|
| SQL injection | ORM parameterizes everything; never build raw SQL with f-strings |
| XSS | Templates auto-escape by default; avoid `\|safe`/`mark_safe`, use `format_html()` |
| CSRF | `CsrfViewMiddleware` + `{% csrf_token %}` on every form |
| Broken auth | Password hashing built in; add rate limiting (below) |
| Security misconfiguration | `check --deploy` (below) |
| Sensitive data exposure | `.env` + `.env.example`, never commit secrets |
| Broken access control | Permission classes/mixins; 404 (not 403) for "not yours" |

## check --deploy

```bash
python manage.py check --deploy
```
Runs checks that are OFF by default (too noisy for daily dev), only when
asked. Common findings: `W009` insecure `SECRET_KEY`, `W018` `DEBUG=True`,
`W020` empty `ALLOWED_HOSTS`, `W004/W008/W012/W016` missing HTTPS-only
cookie/HSTS/redirect settings.

## Secrets via .env

```python
# settings.py
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")   # no-op if missing

SECRET_KEY = os.environ.get("SECRET_KEY", "<dev-only fallback>")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
```
`.env` → gitignored, real values. `.env.example` → committed, placeholders.

## Production-only security settings

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000   # start lower (e.g. 3600) the first time on a real domain
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```
Gate on `DEBUG` — these assume HTTPS, which local `runserver` doesn't have.

## DRF throttling

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/minute", "user": "100/minute"},
}
```
Per-endpoint rate (e.g. login): `ScopedRateThrottle` + `throttle_scope = "..."` on the view + a `"scopes"` rate.

**Gotcha:** `SimpleRateThrottle.THROTTLE_RATES` is a class attribute read
from settings ONCE at import time — overriding `DEFAULT_THROTTLE_RATES`
mid-test-suite won't change it if the throttle class already imported
earlier. Test against the real configured rate instead of shrinking it
per-test.

## Upload size validation

```python
def validate_image_size(image_file):
    if image_file.size > MAX_SIZE_BYTES:
        raise ValidationError("Too large.")

image = models.ImageField(upload_to="...", validators=[validate_image_size])
```
An `ImageField` alone only validates it's a real image (via Pillow) —
not that it's a *reasonable size*. No limit = disk-fill/worker-exhaustion
DoS vector, even behind a permission check.

## Settings-resolved-once, again (Module 13 callback)

A conditional block in `settings.py` (`if not DEBUG: ...`) runs exactly
once, using the environment at process startup. Overriding just the
condition later (`settings.DEBUG = False` in a test) does NOT re-run the
block — override every setting the block would have set, individually,
if you need to simulate its effect after the fact.
