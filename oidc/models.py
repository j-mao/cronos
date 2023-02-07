from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    The model for a User. Since we are purely using OIDC authentication, the `username`
    field represents the `sub` claim, while `preferred_username` is an actual human-
    readable username.
    """

    preferred_username = models.CharField(_("User's display username"), max_length=150)
