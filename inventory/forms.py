from django import forms
from django.forms import ModelForm, ModelChoiceField, widgets
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
        widgets = {
            'started_on': widgets.DateInput(attrs={'type': 'date'}),
            'ended_on': widgets.DateInput(attrs={'type': 'date'}),
        }


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'status', 'notes', 'owner']


class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'notes', 'frame']
        widgets = {
            'date': widgets.DateInput(attrs={'type': 'date'}),
        }
