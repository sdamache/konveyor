from django.db import models
from django.contrib.auth.models import User
from konveyor.apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    """
    User profile to store additional user information
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
