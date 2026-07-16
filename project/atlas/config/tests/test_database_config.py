import subprocess
import sys

# A subprocess, not the `settings` fixture: DATABASES is decided once, at
# settings.py's very first import in this process (already long done by
# the time any test runs) — exactly the "settings resolved once" lesson
# from Modules 13 and 15. Overriding os.environ or settings.POSTGRES_DB
# inside a running test can't rewind and re-run that decision; only a
# genuinely fresh Python process, with the env var already set before
# Django ever imports settings.py, actually exercises this branch.
_PROBE = (
    "import django; django.setup(); "
    "from django.conf import settings; "
    "print(settings.DATABASES['default']['ENGINE'])"
)


def _database_engine(extra_env):
    import os

    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings", **extra_env}
    result = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env, check=True
    )
    return result.stdout.strip()


def test_defaults_to_sqlite_with_no_postgres_env_vars():
    assert _database_engine({"POSTGRES_DB": ""}) == "django.db.backends.sqlite3"


def test_switches_to_postgres_when_postgres_db_is_set():
    engine = _database_engine({
        "POSTGRES_DB": "atlas", "POSTGRES_USER": "atlas", "POSTGRES_PASSWORD": "x",
    })
    assert engine == "django.db.backends.postgresql"
