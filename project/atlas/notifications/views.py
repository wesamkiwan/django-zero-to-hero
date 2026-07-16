from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        # Every user only ever sees their OWN notifications — never
        # filtering by anything the client sends, so there's no way to
        # request someone else's by guessing an ID.
        return Notification.objects.filter(recipient=self.request.user)


@login_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(request.POST.get("next") or reverse_lazy("notifications:list"))


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.POST.get("next") or reverse_lazy("notifications:list"))
