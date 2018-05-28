from django import forms
from django.forms import ModelForm
from .models import Camera, Roll


class CameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format', 'owner']


class RollForm(ModelForm):
    class Meta:
        model = Roll
        fields = ['notes']
