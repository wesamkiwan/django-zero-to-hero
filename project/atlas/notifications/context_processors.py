from .models import Notification


def unread_count(request):
    """Adds {{ unread_notification_count }} to every template's context —
    registered in settings.py's TEMPLATES OPTIONS so base.html's navbar
    bell can show it without every view remembering to pass it in."""
    if not request.user.is_authenticated:
        return {}

    return {
        "unread_notification_count": Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
    }
