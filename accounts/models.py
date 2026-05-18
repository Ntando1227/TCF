from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('operations', 'Operations'),
        ('finance', 'Finance'),
        ('client', 'Client'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='viewer'
    )

    company_name = models.CharField(
        max_length=255,
        blank=True
    )

    phone_number = models.CharField(
        max_length=50,
        blank=True
    )

    must_change_password = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.username
