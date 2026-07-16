from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Atlas's own User model, swapped in via AUTH_USER_MODEL from day one
    of this module — see settings.py and the lesson for why this has to
    happen before any migration touching the user model is applied."""

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        SALES_REP = "sales_rep", "Sales Rep"
        MANAGER = "manager", "Manager"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)

    @property
    def is_manager(self):
        return self.is_superuser or self.role == self.Role.MANAGER

    @property
    def is_sales_rep(self):
        return self.is_manager or self.role == self.Role.SALES_REP
