import io

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def test_check_deploy_passes_when_production_settings_are_set(settings):
    """`python manage.py check --deploy` is the exact command a real
    deployment checklist runs before going live — this proves the
    settings this course adds actually satisfy it, not just that they
    "look" secure.

    Overrides every relevant setting directly here rather than just
    settings.DEBUG (which is what actually drives the `if not DEBUG:`
    block in settings.py) — because DEBUG was already resolved from the
    environment once, at process startup, before this test ever ran.
    Flipping settings.DEBUG now doesn't retroactively re-run that
    conditional block, for the exact reason Module 13's lesson covers:
    settings are resolved once, at import time.
    """
    settings.DEBUG = False
    settings.SECRET_KEY = "a-properly-random-key-that-is-at-least-fifty-characters-long-xyz"
    settings.ALLOWED_HOSTS = ["atlas.example"]
    settings.SECURE_SSL_REDIRECT = True
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True
    settings.SECURE_HSTS_SECONDS = 31536000
    settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    settings.SECURE_HSTS_PRELOAD = True

    out = io.StringIO()
    call_command("check", deploy=True, stdout=out, stderr=out)

    assert "no issues" in out.getvalue()


def test_check_deploy_flags_the_course_defaults():
    """The flip side: confirms check --deploy actually DOES catch the
    convenience defaults this project ships with for local dev (the
    "django-insecure-" SECRET_KEY, no HTTPS-only cookie/HSTS settings) —
    proving the check is a real safety net, not just security theater
    nobody's verified actually fires.

    Doesn't assert on security.W018 (DEBUG=True) or W020 (empty
    ALLOWED_HOSTS): pytest-django itself forces DEBUG=False and Django's
    test runner appends "testserver" to ALLOWED_HOSTS, both globally, for
    the whole session — neither can be observed failing from inside the
    test suite, only in an actual fresh environment. This is the same
    settings-resolved-once lesson from Module 13: settings.py's own
    `if not DEBUG:` block already ran, using the real DEBUG at process
    startup, before pytest-django's later override of settings.DEBUG —
    which is exactly why the HSTS/cookie settings below still show up as
    missing even though `settings.DEBUG` now reads False.
    """
    out = io.StringIO()
    call_command("check", deploy=True, stdout=out, stderr=out)

    output = out.getvalue()
    assert "security.W009" in output  # insecure SECRET_KEY
    assert "security.W012" in output  # SESSION_COOKIE_SECURE never set — the if-not-DEBUG block never ran
