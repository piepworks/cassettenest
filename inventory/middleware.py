import pytz
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render
from .models import Profile


class TimezoneMiddleware:
    """
    Automatically set the timezone to what's set on the User's profile.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                tzname = request.user.profile.timezone
                if tzname:
                    timezone.activate(pytz.timezone(tzname))
                else:
                    timezone.activate(pytz.timezone(settings.TIME_ZONE))
            except Profile.DoesNotExist:
                timezone.activate(pytz.timezone(settings.TIME_ZONE))
        else:
            timezone.deactivate()

        return self.get_response(request)


class HostnameRedirectMiddleware:
    # This is to catch visits from the default hostname for DigitalOcean.
    #
    # Adapted from:
    # https://adamj.eu/tech/2020/03/02/how-to-make-django-redirect-www-to-your-bare-domain/

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(":")[0]
        if host == "cassettenest-p8pny.ondigitalocean.app":
            return HttpResponsePermanentRedirect(
                "https://app.cassettenest.com" + request.path
            )
        else:
            return self.get_response(request)


class MaintenanceModeMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.MAINTENANCE_MODE and not request.user.is_staff:
            response = render(request, "maintenance-mode.html")
            return response
