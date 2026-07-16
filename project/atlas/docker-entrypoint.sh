#!/bin/sh
set -e

# Postgres accepting TCP connections doesn't mean it's finished its own
# startup/recovery — showmigrations has to actually query the
# django_migrations table, so retrying IT (not just a socket connect,
# and not a fixed sleep guessing "long enough") is what proves the
# database is genuinely ready to use.
if [ -n "$POSTGRES_DB" ]; then
    echo "Waiting for Postgres..."
    until python manage.py showmigrations > /dev/null 2>&1; do
        sleep 1
    done
    echo "Postgres is up."
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
