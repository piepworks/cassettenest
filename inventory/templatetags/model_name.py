# Get the model name of an object.
# https://stackoverflow.com/a/6572002
from django.template.defaulttags import register


@register.filter
def model_name(value):
    return value.__class__.__name__
