from django import forms
from django.forms import ModelForm, ModelChoiceField, widgets
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import (
    Camera,
    CameraBack,
    Roll,
    Stock,
    Manufacturer,
    Project,
    Journal,
    User,
    Profile,
    Frame,
    Film,
)
from .utils import apertures, shutter_speeds, film_formats


class UniqueEmailForm:
    # https://gist.github.com/gregplaysguitar/1184995#file-upgrade_user_admin-py-L44-L53
    def clean_email(self):
        qs = User.objects.filter(email=self.cleaned_data["email"])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.count():
            raise forms.ValidationError("That email address is already in use")
        else:
            return self.cleaned_data["email"]


class RegisterForm(UniqueEmailForm, UserCreationForm):
    # Make the email field required.
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class CameraChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CameraForm(ModelForm):
    unavailable = forms.BooleanField(
        label="Unavailable",
        required=False,
        help_text="""
            Keep this camera in your collection, but prevent it from being
            available to load. Good for cameras you no longer own or only
            borrowed.
        """,
    )

    class Meta:
        model = Camera
        fields = [
            "name",
            "format",
            "notes",
            "multiple_backs",
            "unavailable",
        ]


class CameraBackForm(ModelForm):
    unavailable = forms.BooleanField(
        label="Unavailable",
        required=False,
        help_text="""
            Keep this camera back in your collection, but prevent it from being
            available to load. Good for cameras backs you no longer own or only
            borrowed.
        """,
    )

    class Meta:
        model = CameraBack
        fields = [
            "name",
            "notes",
            "format",
            "unavailable",
        ]


class RollForm(ModelForm):
    class Meta:
        model = Roll
        exclude = ["film", "owner", "created_at", "updated_at"]
        widgets = {
            "started_on": widgets.DateInput(attrs={"type": "date"}),
            "ended_on": widgets.DateInput(attrs={"type": "date"}),
        }


class StockForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(StockForm, self).__init__(*args, **kwargs)
        self.fields["manufacturer"] = forms.ModelChoiceField(
            queryset=Manufacturer.objects.all().exclude(
                Q(personal=True) & ~Q(added_by=self.user)
            ),
            required=False,
        )
        self.fields["iso"].max_value = 10000

    new_manufacturer = forms.CharField(
        label="Or add a new manufacturer",
        required=False,
    )
    formats = forms.MultipleChoiceField(
        choices=film_formats,
        initial="135",
        widget=forms.CheckboxSelectMultiple,
        help_text="Choose at least one.",
        error_messages={"required": "Please choose at least one format."},
    )
    destination = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Stock
        fields = [
            "manufacturer",
            "destination",
            "new_manufacturer",
            "name",
            "type",
            "formats",
            "iso",
            "url",
            "description",
        ]

    def clean(self):
        cleaned_data = super().clean()
        new_manufacturer = cleaned_data.get("new_manufacturer")
        manufacturer = cleaned_data.get("manufacturer")

        if not (manufacturer or new_manufacturer):
            raise ValidationError(
                "Please choose an existing manufacturer or add a new one."
            )


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ["name", "status", "notes"]


class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ["date", "notes", "frame"]
        widgets = {
            "date": widgets.DateInput(attrs={"type": "date"}),
        }


class FrameForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FrameForm, self).__init__(*args, **kwargs)
        self.fields["aperture"].label = "Or enter an aperture."
        self.fields["shutter_speed"].label = "Or enter a shutter speed."

    ending_number = forms.IntegerField(
        label="Ending number",
        initial=0,
        help_text="Apply the same settings to all the frames in this range.",
        min_value=0,
        max_value=100,
        required=False,
    )
    aperture_preset = forms.ChoiceField(
        choices=apertures, label="Aperture", required=False
    )
    shutter_speed_preset = forms.ChoiceField(
        choices=shutter_speeds, label="Shutter speed", required=False
    )

    class Meta:
        model = Frame
        fields = [
            "number",
            "date",
            "ending_number",
            "aperture_preset",
            "aperture",
            "shutter_speed_preset",
            "shutter_speed",
            "notes",
        ]
        widgets = {
            "date": widgets.DateInput(attrs={"type": "date"}),
        }


class ReadyForm(forms.Form):
    lab = forms.CharField(required=False, help_text="Or “Self”, “Home”, etc.")
    scanner = forms.CharField(required=False)
    notes_on_development = forms.CharField(
        required=False,
        help_text="Chemicals used, development times, etc.",
        widget=forms.Textarea,
    )


class UserForm(UniqueEmailForm, ModelForm):
    # Make the email field required.
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["timezone", "color_preference"]


class PatternsForm(forms.Form):
    # This form is just to show examples of each field type.

    help_text = "This is help text."

    number = forms.IntegerField(
        initial=1,
        max_value=5,
        help_text='Max value set to "5", minimum is the default "0".',
    )
    text = forms.CharField()
    email = forms.EmailField(help_text=help_text)
    password = forms.CharField(help_text=help_text, widget=widgets.PasswordInput())
    url = forms.URLField(label="URL", help_text=help_text)
    date_input = forms.DateField(
        help_text=help_text, widget=widgets.DateInput(attrs={"type": "date"})
    )
    textarea = forms.CharField(help_text=help_text, widget=forms.Textarea)
    choice = forms.ChoiceField(
        help_text=help_text,
        choices=[
            ("1", "First Option"),
            ("2", "Second Option"),
            ("3", "Third and Final Option"),
        ],
    )
    checkbox = forms.BooleanField(help_text=help_text, required=False)
    multiple_checkboxes = forms.MultipleChoiceField(
        help_text=help_text,
        choices=[("1", "Checkbox 1"), ("2", "Checkbox 2"), ("3", "Checkbox 3")],
        widget=forms.CheckboxSelectMultiple,
    )
    radio = forms.ChoiceField(
        help_text=help_text,
        choices=[("1", "Radio 1"), ("2", "Radio 2"), ("3", "Radio 3")],
        widget=forms.RadioSelect,
    )


class UploadCSVForm(forms.Form):
    csv = forms.FileField()


class FilmForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stock"].required = True

    class Meta:
        model = Film
        exclude = [
            "iso",
            "manufacturer",
            "type",
            "slug",
            "name",
            "url",
        ]


class StepperForm(forms.Form):
    quantity = forms.IntegerField(initial=1, min_value=1)
