import pytest
from django.core.cache import cache

pytestmark = pytest.mark.django_db

# Testing against settings.py's REAL configured rates (20/minute anon,
# 100/minute user) rather than overriding REST_FRAMEWORK per-test: DRF's
# throttle classes read DEFAULT_THROTTLE_RATES into a class attribute
# once, the first time rest_framework.throttling is imported — a
# per-test settings override doesn't retroactively change an
# already-bound class attribute, only a fresh process would see it. The
# exact same class of bug as Module 13's Celery config-caching story:
# something reads a Django setting once, early, and caches it.
ANON_RATE = 20


def test_anonymous_requests_are_throttled_past_the_configured_rate(api_client):
    cache.clear()  # LocMemCache persists for the whole test process, not per-test

    responses = [api_client.get("/api/products/") for _ in range(ANON_RATE + 1)]

    assert all(r.status_code == 200 for r in responses[:ANON_RATE])
    assert responses[ANON_RATE].status_code == 429


def test_authenticated_requests_have_their_own_higher_limit(api_client, admin_user):
    cache.clear()
    api_client.force_authenticate(user=admin_user)

    # More requests than the anon rate would allow — proves a logged-in
    # user is throttled against "user" (100/minute), not lumped in with
    # "anon" (20/minute).
    responses = [api_client.get("/api/products/") for _ in range(ANON_RATE + 1)]

    assert all(r.status_code == 200 for r in responses)
