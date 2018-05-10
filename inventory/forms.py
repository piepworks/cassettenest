from django import forms
from django.forms import ModelForm
from .models import Film
from django.db.models import Count
from .vendor.grouped import GroupedModelChoiceField


class RollCounts(forms.ModelChoiceField):
    def __init__(self, *, choices=(), **kwargs):
        super().__init__(**kwargs)
        self.choices = choices

    def clean(self, value):
        try:
            return Film.objects.all()
        except:
            raise ValidationError


class LoadCameraForm(ModelForm):
    roll_counts = GroupedModelChoiceField(\
        label='Pick a film to load',\
        queryset=None,\
        group_by_field='get_type_display')

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
