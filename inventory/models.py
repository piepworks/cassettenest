import datetime
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .utils import status_number, film_types, film_formats, push_pull_to_db


class Profile(models.Model):
    class ColorModes(models.TextChoices):
        AUTO = ("auto", _("Automatic"))
        LIGHT = ("light", _("Light"))
        DARK = ("dark", _("Dark"))

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=40,
        blank=True,
        choices=settings.TIME_ZONES,
        default=settings.TIME_ZONE,
    )
    color_preference = models.CharField(
        max_length=5,
        choices=ColorModes.choices,
        default=ColorModes.AUTO,
    )
    donation = models.BooleanField(
        default=False,
        help_text="This person has given us money",
    )

    def __str__(self):
        return "Settings for %s" % self.user


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # This apparently works since the user record is updated on every login
    # (last_login)
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
        instance.profile.save()


class Manufacturer(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    personal = models.BooleanField(
        default=False,
        help_text="For user-submitted films. Only visible to the user who added it if this is true.",
    )
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    url = models.URLField(max_length=200, blank=True, verbose_name="URL")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stock(models.Model):
    TYPE_CHOICES = film_types
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="c41",
    )
    name = models.CharField(
        max_length=50,
        help_text="""
            The name of the film stock itself without the manufacturer’s name (unless that’s part of the film’s name.)
        """,
    )
    slug = models.SlugField(max_length=50, unique=True)
    iso = models.PositiveSmallIntegerField(default=100, verbose_name="ISO")
    url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name="URL",
        help_text="Any website that describes this film stock, hopefully from the manufacturer themselves.",
    )
    description = models.TextField(
        blank=True, help_text="Any details about the film or how best to use it."
    )
    personal = models.BooleanField(
        default=False,
        help_text="For user-submitted stocks. Only visible to the user who added it if this is true.",
    )
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["manufacturer__name", "name"]
        unique_together = (
            (
                "manufacturer",
                "name",
            ),
        )

    def __str__(self):
        return f"{self.manufacturer} {self.name}"

    def get_absolute_url(self):
        return reverse(
            "stock",
            args=(
                self.manufacturer.slug,
                self.slug,
            ),
        )


class Film(models.Model):
    TYPE_CHOICES = film_types
    FORMAT_CHOICES = film_formats
    manufacturer = models.ForeignKey(
        Manufacturer, blank=True, null=True, on_delete=models.CASCADE
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        blank=True,
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default="135",
    )
    stock = models.ForeignKey(Stock, blank=True, null=True, on_delete=models.CASCADE)
    iso = models.IntegerField(blank=True, null=True, verbose_name="ISO")
    name = models.CharField(
        blank=True,
        max_length=50,
        help_text="""
            The name of the film itself without the manufacturer’s name (unless that’s part of the film’s name.)
        """,
    )
    slug = models.SlugField(max_length=50, blank=True)
    url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name="URL",
        help_text="Any website that describes this film, hopefully from the manufacturer themselves.",
    )
    description = models.TextField(
        blank=True, help_text="Any details about the film or how best to use it."
    )
    personal = models.BooleanField(
        default=False,
        help_text="For user-submitted films. Only visible to the user who added it if this is true.",
    )
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["manufacturer__name", "name"]
        unique_together = (
            (
                "stock",
                "format",
            ),
        )

    def __str__(self):
        if self.stock:
            name = self.stock
        else:
            name = f"{self.manufacturer} {self.name}"

        return f"{name} in {self.get_format_display()}"

    def get_absolute_url(self):
        if self.stock:
            return reverse(
                "film-rolls",
                args=(
                    self.stock.slug,
                    self.format,
                ),
            )
        else:
            return reverse("film-slug-redirect", args=(self.slug,))


class Camera(models.Model):
    """
    A person's camera.
    Not doing a manufacturer field because I want to leave this very freeform.
    Call a camera "Bernice" if you want.
    """

    STATUS_CHOICES = (
        ("empty", "Empty"),
        ("loaded", "Loaded"),
        ("unavailable", "Unavailable"),
    )
    FORMAT_CHOICES = film_formats
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default="135",
    )
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="empty",
    )
    multiple_backs = models.BooleanField(
        default=False,
        help_text="""
            Select this option if you have multiple interchangeable film
            cassette backs for this camera that can be swapped mid-roll.
        """,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("owner", "name"),)
        ordering = ["status", "name"]

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse("camera-detail", args=(self.id,))

    def get_finished_rolls(self):
        return (
            Roll.objects.filter(camera=self)
            .exclude(status=status_number("loaded"))
            .count()
        )


class CameraBack(models.Model):
    """
    Backs to load with film (instead of a camera directly) for compatible
    cameras (ones with multiple_backs=True).
    """

    # Identical to STATUS_CHOICES on the Camera model.
    STATUS_CHOICES = (
        ("empty", "Empty"),
        ("loaded", "Loaded"),
        ("unavailable", "Unavailable"),
    )
    # Identical to FORMAT_CHOICES on the Camera model.
    FORMAT_CHOICES = film_formats
    camera = models.ForeignKey(
        Camera, on_delete=models.CASCADE, related_name="camera_backs"
    )
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="empty",
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default="120",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s, Back “%s”" % (self.camera, self.name)

    def get_absolute_url(self):
        return reverse("camera-back-detail", args=(self.camera.id, self.id))


class Project(models.Model):
    """
    A subset of rolls to use during a project or trip.
    """

    STATUS_CHOICES = (
        ("current", "Current"),
        ("archived", "Archived"),
    )

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="current",
    )
    cameras = models.ManyToManyField(
        Camera,
        blank=True,
        # Figure out a way to limit this to only cameras from the same owner.
        # limit_choices_to={}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("owner", "name"),)
        ordering = ["-status"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project-detail", args=(self.id,))

    def get_rolls_remaining(self):
        return Roll.objects.filter(
            project=self,
            status=status_number("storage"),
        ).count()


class Roll(models.Model):
    STATUS_CHOICES = (
        ("01_storage", "Storage"),
        ("02_loaded", "Loaded"),
        ("03_shot", "Shot"),
        ("04_processing", "Processing"),
        ("05_processed", "Processed"),
        ("06_scanned", "Scanned"),
        ("07_archived", "Archived"),
    )
    PUSH_PULL_CHOICES = (
        ("-2", "Pull 2 stops"),
        ("-1", "Pull 1 stop"),
        ("+1", "Push 1 stop"),
        ("+2", "Push 2 stops"),
        ("+3", "Push 3 stops"),
    )
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(
        Camera,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    camera_back = models.ForeignKey(
        # If `camera_back` is set, `camera` must be set as well.
        CameraBack,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    lens = models.CharField(
        max_length=255,
        help_text="(or lenses)",
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    code = models.CharField(
        max_length=100,
        help_text="A unique identifier (per year)",
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=status_number("storage"),
    )
    push_pull = models.CharField(
        max_length=2,
        choices=PUSH_PULL_CHOICES,
        blank=True,
        verbose_name="Push/Pull",
        help_text="Push (postive) or pull (negative) by this many stops",
    )
    location = models.CharField(
        max_length=255,
        help_text="(or locations)",
        blank=True,
    )
    notes = models.TextField(blank=True, help_text="General notes")
    lab = models.CharField(
        max_length=255,
        help_text="The name of the lab (or Self, Home, etc.)",
        blank=True,
    )
    scanner = models.CharField(max_length=255, blank=True)
    notes_on_development = models.TextField(
        help_text="Chemicals used, development times, techniques, etc.",
        blank=True,
    )
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.code is not None and self.started_on:
            return "%s / %s" % (self.code, self.started_on.strftime("%Y"))
        else:
            return "%s added on %s" % (self.film, self.created_at.strftime("%Y-%m-%d"))

    @property
    def effective_iso(self):
        "Calculates the effective ISO for a pushed or pulled roll."

        # Using a dictionary as a case/switch statement.
        if self.film.stock:
            return {
                "": self.film.stock.iso,
                "-2": int(self.film.stock.iso * 0.25),
                "-1": int(self.film.stock.iso * 0.5),
                "+1": self.film.stock.iso * 2,
                "+2": self.film.stock.iso * 4,
                "+3": self.film.stock.iso * 8,
            }[self.push_pull]
        else:
            return {
                "": self.film.iso,
                "-2": int(self.film.iso * 0.25),
                "-1": int(self.film.iso * 0.5),
                "+1": self.film.iso * 2,
                "+2": self.film.iso * 4,
                "+3": self.film.iso * 8,
            }[self.push_pull]

    def save(self, *args, **kwargs):
        # Adjust push_pull to translate from the [type=number] field to the proper
        # PUSH_PULL_CHOICES options.
        self.push_pull = push_pull_to_db(self.push_pull)

        # If the started_on field has been populated and the `code` field has
        # not, populate the code field:
        #
        # [format]-[type]-[sequence]
        #
        # 1. Get the format from `film.format`
        # 2. Get the type from `film.type`
        # 3. Query the Roll table to count everything with that format and type
        #    within the year of the `started_on` field. Add one to that number.
        if not self.code and self.started_on:
            sequence = (
                Roll.objects.filter(film__stock__type=self.film.stock.type)
                .filter(film__format=self.film.format)
                .filter(started_on__year=self.started_on.year)
                .filter(owner=self.owner)
                .count()
                + 1
            )

            format = "35" if self.film.format == "135" else self.film.format

            # TODO: Check for proper validation of the code field somehow?
            self.code = "%s-%s-%d" % (format, self.film.stock.type, sequence)
            if self.status == status_number("storage"):
                self.status = status_number("loaded")

        # If we change the status from loaded to any status other than storage,
        # 1. Unload the associated camera (and perhaps camera_back).
        # 2. Set ended_on
        if (
            self.code
            and self.status not in [status_number("storage"), status_number("loaded")]
            and self.ended_on is None
        ):
            # If the camera is still loaded with this roll, unload it.
            if self.camera.status == "loaded":
                camera_roll = Roll.objects.filter(
                    camera=self.camera, status=status_number("loaded")
                )[0]

                if camera_roll == self:
                    self.camera.status = "empty"
                    self.camera.save()

            # If the camera back is still loaded with this roll, unload it.
            if self.camera_back and self.camera_back.status == "loaded":
                camera_roll = Roll.objects.filter(
                    camera_back=self.camera_back, status=status_number("loaded")
                )[0]

                if camera_roll == self:
                    self.camera_back.status = "empty"
                    self.camera_back.save()

            self.ended_on = datetime.date.today()

        # If we’ve loaded this roll, set the associated camera’s (and perhaps
        # camera_back’s) status to 'loaded'.
        if self.status == status_number("loaded"):
            if self.camera.status == "empty":
                self.camera.status = "loaded"
                self.camera.save()

            if self.camera_back and self.camera_back.status == "empty":
                self.camera_back.status = "loaded"
                self.camera_back.save()

            # If we’re changing the status to 'loaded' but it has an ended_on
            # set, clear it. This is if you accidentally changed something
            # from loaded and want to get it back.
            if self.ended_on is not None:
                self.ended_on = None

        # If we’ve changed our minds and put something back into storage, set
        # everything back to factory condition.
        if self.code and self.status == status_number("storage"):
            # Unload camera
            if self.camera:
                self.camera.status = "empty"
                self.camera.save()
                self.camera = None

            # Unload back
            if self.camera_back:
                self.camera_back.status = "empty"
                self.camera_back.save()
                self.camera_back = None

            self.code = ""
            self.push_pull = ""
            self.started_on = None
            self.ended_on = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("roll-detail", args=(self.id,))


class Journal(models.Model):
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    frame = models.IntegerField(help_text="Last frame of the day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "journal entry"
        verbose_name_plural = "journal entries"
        unique_together = (("roll", "date"),)
        ordering = ["date"]

    def __str__(self):
        return f'Journal entry for {self.roll.code} on {self.date.strftime("%Y-%m-%d")}'

    @property
    def starting_frame(self):
        "Adds one to the previous entry's frame."

        entries = Journal.objects.filter(roll=self.roll)

        for index, obj in enumerate(entries):
            if obj == self:
                if index > 0:
                    # If it's not the first entry for the roll.
                    return entries[index - 1].frame + 1
                else:
                    # If it is the first entry for the roll.
                    return 1


class Frame(models.Model):
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    aperture = models.CharField(
        max_length=20, blank=True, help_text="Preset dropdown will be ignored."
    )
    shutter_speed = models.CharField(
        max_length=20, blank=True, help_text="Preset dropdown will be ignored."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("roll", "number"),)

    def __str__(self):
        return f"Frame #{self.number} of {self.roll}"
