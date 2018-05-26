from django import forms
from django.forms import ModelForm
from .models import Film, Camera


class AddCameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format']
