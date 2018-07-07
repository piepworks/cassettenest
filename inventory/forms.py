from django import forms
from django.forms import ModelForm
from .models import Camera, Roll, Project


class CameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format', 'owner']


class RollNotesForm(ModelForm):
    class Meta:
        model = Roll
        fields = ['notes']


class RollStatusForm(ModelForm):
    class Meta:
        model = Roll
        fields = ['status']


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'notes', 'owner']
