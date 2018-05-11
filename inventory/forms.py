from django import forms
from django.forms import ModelForm
from .models import Film
from django.db.models import Count
from .vendor.grouped import GroupedModelChoiceField

# I wish that this form looked more like this:
# https://gist.github.com/trey/e59218963676ea3058ef15eb9b558d27
# But I went down a rabbit hole trying to figure out how to get it to use the
# queryset from `__init__` and it couldn't. And it doesn't matter right now
# because what we have here works exactly as I want, it's just not that pretty
# and a little hard to understand.

class LoadCameraForm(ModelForm):
    roll_counts = GroupedModelChoiceField(\
        label='Pick a film to load',\
        queryset=None,\
        group_by_field='type')

    class Meta:
        model = Film
        fields = ['roll_counts']

    def __init__(self, *args, owner, format, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['roll_counts'].queryset = Film.objects\
            .filter(roll__owner=owner, roll__status='storage')\
            .filter(format=format)\
            .annotate(count=Count('name'))\
            .order_by('type')
