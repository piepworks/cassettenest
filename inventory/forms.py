from django import forms
from django.forms import ModelForm, ModelChoiceField, widgets
from django.contrib.auth.forms import UserCreationForm
from django.utils.safestring import mark_safe
from .models import Camera, Roll, Project, Journal, User, Profile
import djstripe.models


class RegisterForm(UserCreationForm):
    # Make the email field required.
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CameraChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CameraForm(ModelForm):
    unavailable = forms.BooleanField(
        label='Unavailable',
        required=False,
        help_text='''
            Keep this camera in your collection, but prevent it from being
            available to load. Good for cameras you no longer own or only
            borrowed.
        '''
    )

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
    # Make the email field required.
    email = forms.EmailField()

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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['timezone']


class PatternsForm(forms.Form):
    # This form is just to show examples of each field type.

    help_text = 'This is help text.'

    text = forms.CharField()
    email = forms.EmailField(help_text=help_text)
    password = forms.CharField(
        help_text=help_text,
        widget=widgets.PasswordInput()
    )
    date_input = forms.DateField(
        help_text=help_text,
        widget=widgets.DateInput(attrs={'type': 'date'})
    )
    textarea = forms.CharField(
        help_text=help_text,
        widget=forms.Textarea
    )
    number = forms.IntegerField(help_text=help_text)
    choice = forms.ChoiceField(
        help_text=help_text,
        choices=[
            ('1', 'First Option'),
            ('2', 'Second Option'),
            ('3', 'Third and Final Option')
        ]
    )
    checkbox = forms.BooleanField(
        help_text=help_text,
        required=False
    )


class PurchaseSubscriptionForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=djstripe.models.Plan.objects.all())
    stripe_source = forms.CharField(
        max_length="255", widget=forms.HiddenInput(), required=False
    )
