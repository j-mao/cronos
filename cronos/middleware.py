import pytz
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(pytz.timezone("US/Eastern"))
        return self.get_response(request)


class ScriptsRemoteUserMiddleware(RemoteUserMiddleware):
    header = "SSL_CLIENT_S_DN_Email"
