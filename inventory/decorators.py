from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from .utils import is_active, is_inactive


def user_account_active(view_func):
    '''
    For views that are only for people with active accounts:
    Paying customers or those still on an active trial
    '''
    actual_decorator = user_passes_test(
        is_active,
        login_url=reverse_lazy('account-inactive'),
        redirect_field_name=None
    )
    return actual_decorator(view_func)


def user_account_inactive(view_func):
    '''
    For views that are only for people with inactive accounts:
    Their trial is over or their account is cancelled
    '''
    actual_decorator = user_passes_test(
        is_inactive,
        login_url=reverse_lazy('index'),
        redirect_field_name=None
    )
    return actual_decorator(view_func)
