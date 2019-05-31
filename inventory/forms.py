from django import forms
from django.forms import ModelForm, ModelChoiceField
from .models import Camera, Roll, Project, Journal


class CameraChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format', 'owner']


class RollForm(ModelForm):
    class Meta:
        model = Roll
        exclude = ['film', 'owner', 'created_at', 'updated_at']


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'status', 'notes', 'owner']


class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'notes', 'frame']
