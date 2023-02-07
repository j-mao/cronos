from authlib.integrations.django_client import OAuth
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.crypto import get_random_string

oauth = OAuth()
oauth.register(name="mit")

STATE_CODE_LENGTH = 20


def login(request):
    state = get_random_string(STATE_CODE_LENGTH)
    redirect_uri = request.build_absolute_uri(reverse("oidc:authorize") + "?" + request.META["QUERY_STRING"])
    request.session["session_state"] = state
    return oauth.mit.authorize_redirect(request, redirect_uri, state=state)


def authorize(request):
    app_state = request.GET.get("state", "")
    session_state = request.session.get("session_state", "")
    if app_state == session_state:
        token = oauth.mit.authorize_access_token(request)
        userinfo = oauth.mit.userinfo(token=token)
        user = authenticate(request, token=token, userinfo=userinfo)
        if user is not None:
            auth_login(request, user)

    path = request.GET.get(REDIRECT_FIELD_NAME, reverse("registrar:index"))
    return HttpResponseRedirect(path)


def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse("registrar:index"))
