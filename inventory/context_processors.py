import datetime
from django.urls import reverse


def subscription_banner(request):
    user_profile = request.user.profile
    active_subscription = user_profile.has_active_subscription
    trial_days_remaining = user_profile.trial_days_remaining
    subscription_status = user_profile.subscription_status
    settings_url = reverse('settings') + '#subscription'

    messages = {
        'none':       f'Paid plans are now available. Help support this project '
                      f'and <a href="{settings_url}">subscribe</a>!',

        'past_due':   f'Looks like there’s a problem with your subscription. '
                      f'<a href="{settings_url}">Please check your settings.</a>',

        'paused':     f'Your subscription is currently paused. '
                      f'<a href="mailto:boss@treylabs.com">Get in touch</a> if you have questions.',

        'cancelling': f'Your subscription is scheduled to be canceled. '
                      f'<a href="{settings_url}">Update your settings</a> if you change your mind.',

        'cancelled':  f'Your subscription has been cancelled. '
                      f'a href="{settings_url}">Update your settings to resubscribe</a>.',
    }

    # Default to what's in the Profile model.
    status = subscription_status

    if subscription_status == 'deleted':
        cancellation_date = user_profile.paddle_cancellation_date

        if cancellation_date and cancellation_date > datetime.date.today():
            message = messages['cancelling']
        else:
            message = messages['cancelled']
    else:
        message = messages[subscription_status]

    return {
        'subscription_banner': {
            'status': status,
            'message': message,
        }
    }