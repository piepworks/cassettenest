from django import forms
from django.forms import ModelForm
from .models import Camera, Roll, Project


class CameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format', 'owner']


class RollForm(ModelForm):
    class Meta:
        model = Roll
        exclude = ['code', 'film', 'owner', 'created_at', 'updated_at']


class RollProjectForm(ModelForm):
    class Meta:
        model = Roll
        fields = ['project']


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'status', 'notes', 'owner']
