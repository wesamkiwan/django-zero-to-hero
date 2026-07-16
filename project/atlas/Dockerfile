# Slim, not alpine: alpine's musl libc frequently breaks Pillow/psycopg2
# binary wheels, forcing a slower from-source compile — slim (Debian-based)
# gets prebuilt wheels for everything Atlas needs, trading a larger image
# for a much simpler, faster, less fragile build.
FROM python:3.12-slim

# Prevents Python buffering stdout/stderr — without this, `docker logs`
# can lag behind or silently drop output right before a crash, which is
# exactly when you need it most.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# libpq5 — the PostgreSQL client library psycopg2 links against at
# runtime, even though psycopg2-binary bundles its own copy for install;
# some base images still need it present. build-essential covers the
# rare package that has no prebuilt wheel for this exact Python/OS combo.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copied and installed BEFORE the rest of the app: Docker caches each
# layer, so `docker build` only re-runs `pip install` when
# requirements.txt itself changes — editing application code afterward
# doesn't invalidate this (slow) layer and force a full reinstall.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
# The default command entrypoint.sh execs after migrate/collectstatic —
# docker-compose.yml overrides this for the worker/beat services, which
# need `celery`, not `gunicorn`, as their actual process.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
