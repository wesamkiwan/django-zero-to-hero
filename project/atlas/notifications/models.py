from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An in-app notification for a staff User — e.g. "New order #12
    placed", surfaced as a bell icon in the navbar (see
    context_processors.py and base.html). Deliberately not tied to
    Customer: Customers in this CRM aren't necessarily site accounts at
    all, so there'd be nowhere to show a Customer a notification even if
    we wanted to."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # -pk as a tiebreaker: auto_now_add timestamps from two
        # notifications created microseconds apart can land on the same
        # value depending on the database's datetime precision, which
        # would make "-created_at" alone non-deterministic.
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.message
