from django import forms
from django.forms import ModelForm, ModelChoiceField
from .models import Camera, Roll, Project


class CameraChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CameraForm(ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'format', 'owner']


class RollForm(ModelForm):
    camera = CameraChoiceField(queryset=Camera.objects.all(), required=False)

    class Meta:
        model = Roll
        exclude = ['code', 'film', 'owner', 'created_at', 'updated_at']


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'status', 'notes', 'owner']
