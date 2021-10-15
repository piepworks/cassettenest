import datetime
from django.urls import reverse


def subscription_banner(request):
    no_banner = {'subscription_banner': ''}

    if not request.user.is_authenticated:
        return no_banner

    user_profile = request.user.profile
    active_subscription = user_profile.has_active_subscription
    trial_days_remaining = user_profile.trial_days_remaining
    subscription_status = user_profile.subscription_status
    settings_url = reverse('settings') + '#subscription'

    messages = {
        'trial':      f'You have {trial_days_remaining} days left in your free trial. '
                      f'<a href="{settings_url}">Choose a plan.</a>',

        'trial_over': f'Your free trial has ended. '
                      f'Please <a href="{settings_url}">choose a plan</a> to continue to add new stuff!',

        'past_due':   f'Looks like there’s a problem with your subscription. '
                      f'<a href="{settings_url}">Please check your settings.</a>',

        'paused':     f'Your subscription is currently paused. '
                      f'<a href="mailto:boss@treylabs.com">Get in touch</a> if you have questions.',

        'cancelling': f'Your subscription is scheduled to be canceled. '
                      f'<a href="{settings_url}">Update your settings</a> if you change your mind.',

        'cancelled':  f'Your subscription has been cancelled. '
                      f'a href="{settings_url}">Update your settings to resubscribe</a>.',
    }

    if not active_subscription and subscription_status == 'none':
        if trial_days_remaining > 0:
            message = messages['trial']
        else:
            message = messages['trial_over']
    elif subscription_status != 'none':
        if subscription_status == 'deleted':
            cancellation_date = user_profile.paddle_cancellation_date
            if cancellation_date and cancellation_date > datetime.date.today():
                message = messages['cancelling']
            else:
                message = messages['cancelled']
        else:
            if subscription_status != 'active':
                message = messages[subscription_status]

    if 'message' in locals():
        return {
            'subscription_banner': {
                'status': subscription_status,
                'message': message,
            }
        }
    else:
        return no_banner
