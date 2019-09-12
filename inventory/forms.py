from django import forms
from django.forms import ModelForm, ModelChoiceField, widgets
from django.utils.safestring import mark_safe
from .models import Camera, Roll, Project, Journal, User


class CameraChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CameraForm(ModelForm):
    unavailable = forms.BooleanField(label='Unavailable', required=False)

    class Meta:
        model = Camera
        fields = ['name', 'format', 'notes', 'owner', 'unavailable']


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


class ReadyForm(forms.Form):
    lab = forms.CharField(
        required=False,
        help_text=mark_safe('Or &ldquo;Self&rdquo;, &ldquo;Home&rdquo;, etc.')
    )
    scanner = forms.CharField(required=False)
    notes_on_development = forms.CharField(
        required=False,
        help_text='Chemicals used, development times, etc.',
        widget=forms.Textarea
    )


class UserForm(ModelForm):
    # https://gist.github.com/gregplaysguitar/1184995#file-upgrade_user_admin-py-L44-L53
    def clean_email(self):
        qs = User.objects.filter(email=self.cleaned_data['email'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.count():
            # TODO: actually display this error on the page.
            raise forms.ValidationError('That email address is already in use')
        else:
            return self.cleaned_data['email']

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
