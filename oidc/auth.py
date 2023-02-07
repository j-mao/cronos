from django.contrib.auth.backends import BaseBackend

from .models import User


class OpenIDCBackend(BaseBackend):
    def authenticate(self, request, token=None, userinfo=None):
        match userinfo:
            case {
                "sub": sub,
                "preferred_username": preferred_username,
                "given_name": first_name,
                "family_name": last_name,
                "email": email,
            }:
                user, created = User.objects.get_or_create(username=sub)
                if created:
                    user.preferred_username = preferred_username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email
                    user.save()
                return user
            case _:
                return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
