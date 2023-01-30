# http://web.mit.edu/snippets/django/mit/__init__.py
# Licensed under the MIT License

import ldap
import ldap.filter
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.backends import RemoteUserBackend
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse


class ScriptsRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username):
        if "@" in username:
            name, domain = username.split("@")
            assert domain.upper() == "MIT.EDU"
            return name
        else:
            return username

    def configure_user(self, request, user):
        username = user.username
        user.set_unusable_password()
        con = ldap.initialize("ldap://ldap-too.mit.edu")
        con.simple_bind_s("", "")
        dn = "dc=mit,dc=edu"
        fields = ["cn", "sn", "givenName", "mail", ]
        userfilter = ldap.filter.filter_format("uid=%s", [username])
        result = con.search_s(dn, ldap.SCOPE_SUBTREE, userfilter, fields)
        if len(result) == 1:
            user.first_name = result[0][1]["givenName"][0].decode()
            user.last_name = result[0][1]["sn"][0].decode()
            try:
                user.email = result[0][1]["mail"][0].decode()
            except KeyError:
                user.email = username + "@mit.edu"
        else:
            raise ValueError(f"Could not find user with username '{username}' (filter '{userfilter}')")
        user.save()
        return user


@transaction.atomic
def get_or_create_mit_user(username):
    """
    Given an MIT username, return a Django user object for them.
    If necessary, create (and save) the Django user for them.
    If the MIT user doesn"t exist, raises ValueError.
    """
    user, created = get_user_model().objects.get_or_create(username=username)
    if created:
        backend = ScriptsRemoteUserBackend()
        # Raises ValueError if the user doesn't exist
        try:
            return backend.configure_user(None, user), created
        except ValueError:
            user.delete()
            raise
    else:
        return user, created


def kerberos_login(request, **kwargs):
    host = request.META["HTTP_HOST"].split(":")[0]
    if request.META["SERVER_PORT"] == "444":
        if request.user.is_authenticated:
            # They're already authenticated --- go ahead and redirect
            redirect_field_name = kwargs.get("redirect_field_name", REDIRECT_FIELD_NAME)
            redirect_to = request.GET.get(redirect_field_name, "")
            if not redirect_to or "//" in redirect_to or " " in redirect_to:
                redirect_to = reverse("registrar:index")
            return HttpResponseRedirect(redirect_to)
        else:
            return render(request, "registrar/login_required.html")
    else:
        # Move to port 444
        redirect_to = f"https://{host}:444{request.get_full_path()}"
        return HttpResponseRedirect(redirect_to)
