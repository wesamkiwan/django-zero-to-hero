# Module 16 — Configuration, Docker & Deployment

> **Where we're going:** Atlas stops being "a project that runs on my
> machine" and becomes a project that runs the **same way everywhere** —
> a real PostgreSQL database instead of SQLite, Gunicorn instead of
> `runserver`, Nginx in front of it, Celery worker/beat as their own
> containers, all wired together with Docker Compose, plus CI that proves
> it on every push. Module 15's `.env` pattern is what makes all of this
> almost boring to wire up.
>
> **A note on how this module was built:** every other module in this
> course was verified by actually running it — `pytest`, `runserver`, a
> real browser. This one's Docker artifacts (the `Dockerfile`,
> `docker-compose.yml`, Nginx config, entrypoint script) were written
> carefully but **could not be run end-to-end in the environment that
> built them** (no Docker daemon available there). Treat this module's
> hands-on section as required, not optional — run `docker compose up`
> yourself and fix anything that doesn't match your machine before
> trusting this as a template for a real deployment.

## 1. One settings file, two databases

```python
# config/settings.py
if os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
```

No `POSTGRES_DB` set → SQLite, zero setup, exactly like every earlier
module and the test suite. `POSTGRES_DB` set (which `docker-compose.yml`
does, for every container) → the real PostgreSQL that Compose runs. Not
a special "Docker mode" — the exact same pattern Module 15 already
established for `SECRET_KEY`/`DEBUG`: read from the environment, sensible
local fallback.

**Verifying this without a live Postgres**, and without the exact
gotcha Modules 13 and 15 both hit:

```python
# config/tests/test_database_config.py
def _database_engine(extra_env):
    result = subprocess.run([sys.executable, "-c", _PROBE], env={**os.environ, **extra_env}, ...)
    return result.stdout.strip()

def test_switches_to_postgres_when_postgres_db_is_set():
    assert _database_engine({"POSTGRES_DB": "atlas", ...}) == "django.db.backends.postgresql"
```

A **subprocess**, deliberately, not the `settings` fixture: `DATABASES`
is decided once, at `settings.py`'s very first import in the *current*
process — long since done by the time any test runs. By now this should
sound familiar: it's the third module in a row where "a setting is
resolved once, at process start" mattered (Module 13's Celery config,
Module 15's `if not DEBUG:` block, now this). Only a genuinely fresh
process — with the env var set *before* Django ever imports
`settings.py` — actually exercises the branch; this test spawns exactly
that.

## 2. Object storage for uploads — the same pattern again

```python
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
# else: Django's own STORAGES default (local disk) applies unchanged.
```

Why this matters and Module 14 didn't need to care yet: a Docker
container's local filesystem is **ephemeral** and not shared between
replicas. An image uploaded to one `web` container wouldn't exist on
another, and vanishes entirely the moment that container is redeployed.
Object storage (S3, or an S3-compatible service like MinIO) fixes both
problems — every container talks to the same external store.

Notice what's *not* set: `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`
aren't wired into Django settings at all. `django-storages` delegates to
`boto3`, which already finds credentials itself (its own env vars, or an
IAM role in a real cloud deployment) — plumbing them through Django
settings too would just be a second, redundant path for the same secret
to leak from.

This course's own `docker-compose.yml` leaves `AWS_STORAGE_BUCKET_NAME`
unset — requiring a real AWS account just to follow along isn't
reasonable, so the demo stack keeps using local disk (via a shared Docker
volume, §4). Flip that one env var, with real AWS credentials available
to boto3, and product images move to S3 with no other code change.

## 3. Docker basics: the Dockerfile

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

Two choices worth calling out:

- **`requirements.txt` is copied and installed *before* the rest of the
  app.** Docker caches each instruction as a layer; editing
  `catalog/views.py` afterward doesn't invalidate the (slow) `pip
  install` layer, since that `COPY requirements.txt .` line's input
  didn't change. Reorder it the other way (`COPY . .` first) and every
  single code change would force a full dependency reinstall on every
  build.
- **`slim`, not `alpine`.** Alpine's musl libc frequently breaks
  Pillow/psycopg2's prebuilt binary wheels, forcing a slow from-source
  compile (or outright failure) — `slim` (Debian-based) gets prebuilt
  wheels for everything Atlas needs. A noticeably larger image is a
  trade worth making for a build that doesn't fight you.

`ENTRYPOINT` + `CMD` split matters for `docker-compose.yml`'s `worker`/
`beat` services (§4): Compose's `command:` replaces `CMD`, but
`ENTRYPOINT` still runs first — so the same migrate/collectstatic setup
happens no matter which process the container ultimately execs into.

```sh
# docker-entrypoint.sh
#!/bin/sh
set -e

if [ -n "$POSTGRES_DB" ]; then
    echo "Waiting for Postgres..."
    until python manage.py showmigrations > /dev/null 2>&1; do
        sleep 1
    done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
```

`showmigrations`, not a raw TCP/ping check: Postgres accepting
connections doesn't mean it's finished its own startup/recovery.
`showmigrations` has to actually **query** the `django_migrations`
table — retrying that (instead of guessing a fixed `sleep 10` is "long
enough") is what proves the database is genuinely ready to use, not just
listening on a socket. `exec "$@"` replaces the shell process with
whatever command was passed (Gunicorn, or Celery for the other
services) — so it becomes PID 1 and receives Docker's shutdown signals
directly, instead of a shell process silently swallowing them.

### A Windows-specific trap this repo already had to guard against

```
# .gitattributes
*.sh text eol=lf
Dockerfile text eol=lf
```

This machine (and probably yours, if you're on Windows) has git's
`core.autocrlf=true` — every earlier module's `.py`/`.html` files were
checked out with Windows line endings, which is invisible and harmless
for those. `docker-entrypoint.sh` is different: its `#!/bin/sh` shebang
line, if it ends in `\r\n` instead of `\n`, becomes literally
`#!/bin/sh\r` — inside the Linux container, that's not a recognized
interpreter path at all, and the container fails immediately with `exec
./docker-entrypoint.sh: no such file or directory`, an error message
that has nothing obviously to do with line endings. `.gitattributes`
forces LF for these two files specifically, regardless of the checking-
out machine's OS or git config.

## 4. Wiring it all together: docker-compose.yml

Five services: `db` (Postgres), `redis`, `web` (Gunicorn), `worker`
(Celery), `beat` (Celery Beat), plus `nginx` in front of `web`.

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    env_file: .env
    healthcheck: ...

  web:
    build: .
    env_file: .env
    environment:
      POSTGRES_HOST: db              # NOT localhost — "db" is the service name
      CELERY_BROKER_URL: redis://redis:6379/0
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      db: {condition: service_healthy}
      redis: {condition: service_healthy}

  worker:
    build: .
    command: celery -A config worker --loglevel=info
    ...

  nginx:
    image: nginx:1.27-alpine
    ports: ["8000:80"]
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
```

`env_file: .env` reuses **the exact same file** Module 15 introduced —
the same `SECRET_KEY`/`DEBUG` a plain `runserver` reads now configures
every container in the stack too. `POSTGRES_HOST: db` (not `localhost`)
is the one thing worth memorizing about Docker networking: containers
reach each other by **service name**, which Docker's internal DNS
resolves automatically — `localhost` inside the `web` container refers
to the `web` container itself, not the `db` container next to it.

`static_volume`/`media_volume` are **shared** between `web` and `nginx` —
`web` writes collected static files and uploaded media into them,
`nginx` reads the same files straight off disk for `/static/`/`/media/`,
never touching Gunicorn/Django for those requests at all:

```nginx
# nginx/default.conf
location /static/ {
    alias /app/staticfiles/;
}
location / {
    proxy_pass http://web:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

This is the actual point of Nginx-in-front-of-Gunicorn: a request for a
CSS file shouldn't wake up a Python worker process at all.

**A known simplification, worth naming rather than hiding:** `worker`
and `beat` inherit the same `ENTRYPOINT`, so they *also* run `migrate`
and `collectstatic` on startup — redundant (three containers doing the
same migration check), and in a real high-traffic deployment, occasionally
risky (two containers running schema-changing migrations at the exact
same instant can contend on locks). A more careful production setup runs
migrations as a single one-off release step, with `web`/`worker`/`beat`
never running them themselves. This course keeps the simpler version —
know the trade-off you're making if you copy this as-is.

## 5. CI: GitHub Actions

```yaml
# .github/workflows/ci.yml
services:
  postgres:
    image: postgres:16-alpine
    env: {POSTGRES_DB: atlas_ci, POSTGRES_USER: atlas_ci, POSTGRES_PASSWORD: atlas_ci}
    ports: ["5432:5432"]

steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with: {python-version: "3.12", cache: pip}
  - run: pip install -r requirements-dev.txt
  - run: python manage.py migrate --noinput
  - run: coverage run -m pytest -v
  - run: coverage report
```

CI runs against a **real Postgres service container**, not SQLite — the
whole reason to bother is that SQLite is lenient about things Postgres
isn't (case sensitivity in some lookups, certain constraint checks), so
"tests pass against SQLite" doesn't actually prove the app works against
the database it's deployed on. A separate `docker-build` job builds (but
doesn't push) the image, catching a broken `Dockerfile` before it ever
reaches a real deploy.

## 6. Hands-on

**This section is the actual verification this module's Docker files
still need** — run it for real:

```bash
cd project/atlas
cp .env.example .env
# edit .env: fill in POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD with real values —
# the Postgres image refuses to start with a blank password.

docker compose up --build
```

Then check:
- `http://localhost:8000/` loads through Nginx → Gunicorn → Django.
- `docker compose logs worker` shows Celery ready and picking up tasks
  (place an order via `/api/orders/` and watch it process).
- `docker compose exec db psql -U <user> -d <db> -c '\dt'` shows Atlas's
  tables — proof it's really talking to Postgres, not silently falling
  back to SQLite.
- Static files (Bootstrap, `custom.css`) load correctly — proof Nginx is
  serving `/static/` itself, not proxying it through to Django.

### Exercise

The migration-redundancy trade-off in §4 is a real, adjustable design
decision — replace it: add a one-off `migrate` service (`docker compose
run --rm migrate`, no `depends_on` from `worker`/`beat`), strip
`migrate`/`collectstatic` out of `docker-entrypoint.sh` for the
`worker`/`beat` services specifically (keeping it for `web`, or moving it
to the new one-off service entirely), and confirm the whole stack still
comes up cleanly with `docker compose up`.

## 7. Checkpoint — you should now be able to:

- [ ] Explain why `DATABASES`/`STORAGES` switch on an environment
      variable's presence rather than a separate "Docker settings" file.
- [ ] Explain why testing that switch needs a subprocess, tying it to
      the same "settings resolved once" lesson from Modules 13 and 15.
- [ ] Write a `Dockerfile` that layers `pip install` before `COPY . .`,
      and explain why the order matters for build speed.
- [ ] Explain why containers reach each other by service name, never
      `localhost`.
- [ ] Explain what Nginx is actually buying you in front of Gunicorn.
- [ ] Explain why CI should test against the same database engine
      production uses, not whatever's most convenient locally.
- [ ] Have actually run `docker compose up --build` yourself and fixed
      anything this module's untested-in-place artifacts got wrong for
      your machine.

## 8. What's next

**Module 17 — Git/Team Workflow, System Design & Job Readiness** is the
capstone: professional Git workflow, the architecture trade-offs made
across this entire course (and the ones deliberately left as an
exercise), interview prep, and presenting Atlas as a portfolio piece.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 17.
