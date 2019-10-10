import pytz
from django.utils import timezone
from django.conf import settings
from .models import Profile


class TimezoneMiddleware:
    '''
    Automatically set the timezone to what's set on the User's profile.
    '''
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
