# Look up a dictionary value with a variable.
# https://stackoverflow.com/a/8000091
from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
