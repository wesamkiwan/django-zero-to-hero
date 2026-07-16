from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # UserCreationForm.Meta.fields is just ("username",) by default —
        # we add email so new accounts have one from the start. Deliberately
        # NOT including "role": public sign-up always creates a Customer
        # (the model's default) — only staff can promote someone to
        # Sales Rep/Manager, via the admin.
        fields = ("username", "email")
