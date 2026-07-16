# Cheat Sheet — Module 16: Configuration, Docker & Deployment

## Env-var-switched settings (same pattern, three times now)

```python
if os.environ.get('POSTGRES_DB'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', ...}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}

if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage"}, ...}
# else: Django's own local-disk default applies
```
No env var → local/SQLite fallback (zero setup). Env var present → the
real backend. Never a separate "Docker settings file."

## Testing a setting resolved once, at import time

```python
def _run_in_subprocess(extra_env):
    return subprocess.run([sys.executable, "-c", PROBE], env={**os.environ, **extra_env}, ...)
```
Only a **fresh process** (env var set before Django imports `settings.py`)
actually exercises a branch like the one above — the `settings` fixture
mid-test can't rewind code that already ran (Modules 13, 15, 16, same lesson).

## Dockerfile essentials

```dockerfile
FROM python:3.12-slim              # not alpine — musl breaks Pillow/psycopg2 wheels
COPY requirements.txt .            # BEFORE the rest of the app — caches the slow layer
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["./docker-entrypoint.sh"]   # always runs first
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]  # compose can override this
```

```sh
#!/bin/sh
set -e
until python manage.py showmigrations > /dev/null 2>&1; do sleep 1; done   # real readiness check, not a ping
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"                           # becomes PID 1 — receives shutdown signals directly
```

## .gitattributes — the Windows line-ending trap

```
*.sh text eol=lf
Dockerfile text eol=lf
```
Without this, `core.autocrlf=true` silently turns `#!/bin/sh` into
`#!/bin/sh\r` on checkout — the container fails with a confusing
"no such file or directory," not an obvious line-ending error.

## docker-compose.yml essentials

```yaml
services:
  web:
    environment:
      POSTGRES_HOST: db            # service name, NEVER localhost
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      db: {condition: service_healthy}
  worker:
    build: .
    command: celery -A config worker --loglevel=info   # overrides CMD, keeps ENTRYPOINT
volumes:
  static_volume:   # shared between web (writes) and nginx (reads)
  media_volume:
```
Containers reach each other by **service name** via Docker's internal
DNS — `localhost` inside a container means that container itself.

## Nginx: static files never touch Django

```nginx
location /static/ { alias /app/staticfiles/; }
location /media/  { alias /app/media/; }
location / { proxy_pass http://web:8000; proxy_set_header Host $host; }
```

## CI against the real database engine

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env: {POSTGRES_DB: atlas_ci, ...}
```
SQLite is lenient about things Postgres isn't — "tests pass on SQLite"
doesn't prove the app works on the database production actually uses.

## Known trade-off: migrations run in every container

`web`/`worker`/`beat` all inherit the same entrypoint, so all three run
`migrate` on startup — simple, but redundant, and a real risk of lock
contention under concurrent schema changes. Production-grade fix: a
single one-off release/migrate step; nothing else runs migrations itself.
