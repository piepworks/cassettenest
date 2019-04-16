from django.db import models
from django.contrib.auth.models import User
from .utils import *
import datetime


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    url = models.URLField(max_length=200, blank=True, verbose_name='URL')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Film(models.Model):
    TYPE_CHOICES = (
        ('c41', 'C41 Color'),
        ('bw', 'Black and White'),
        ('e6', 'E6 Color Reversal'),
    )
    FORMAT_CHOICES = (
        ('135', '35mm'),
        ('120', '120'),
    )
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='c41',
    )
    iso = models.IntegerField(verbose_name='ISO')
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='135',
    )
    url = models.URLField(max_length=200, blank=True, verbose_name='URL')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['manufacturer__name', 'name']

    def __str__(self):
        return '%s %s in %s' % (
            self.manufacturer, self.name, self.get_format_display()
        )


class Camera(models.Model):
    """
    A person's camera.
    Not doing a manufacturer field because I want to leave this very freeform.
    Call a camera "Bernice" if you want.
    """

    STATUS_CHOICES = (
        ('empty', 'Empty'),
        ('loaded', 'Loaded'),
        ('unavailable', 'Unavailable'),
    )
    FORMAT_CHOICES = (
        ('135', '35mm'),
        ('120', '120'),
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='135',
    )
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='empty',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('owner', 'name'),)
        ordering = ['-status', 'name']

    def __str__(self):
        return '%s\'s %s' % (self.owner, self.name)


class Project(models.Model):
    """
    A subset of rolls to use during a project or trip.
    """
    STATUS_CHOICES = (
        ('current', 'Current'),
        ('archived', 'Archived'),
    )

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='current',
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
        unique_together = (('owner', 'name'),)

    def __str__(self):
        return self.name


class Roll(models.Model):
    STATUS_CHOICES = (
        ('01_storage', 'Storage'),
        ('02_loaded', 'Loaded'),
        ('03_shot', 'Shot'),
        ('04_processing', 'Processing'),
        ('05_processed', 'Processed'),
        ('06_scanned', 'Scanned'),
        ('07_archived', 'Archived'),
    )
    PUSH_PULL_CHOICES = (
        ('-2', 'Pull 2 stops'),
        ('-1', 'Pull 1 stop'),
        ('+1', 'Push 1 stop'),
        ('+2', 'Push 2 stops'),
        ('+3', 'Push 3 stops'),
    )
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(
        Camera,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    lens = models.CharField(
        max_length=255,
        help_text='(or lenses)',
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
        help_text='A unique roll code (per year)',
        unique_for_year='started_on',
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=status_number('storage'),
    )
    push_pull = models.CharField(
        max_length=2,
        choices=PUSH_PULL_CHOICES,
        blank=True,
        verbose_name='Push/Pull',
    )
    location = models.CharField(
        max_length=255,
        help_text='(or locations)',
        blank=True,
    )
    notes = models.TextField(blank=True, help_text='General notes')
    lab = models.CharField(
        max_length=255,
        help_text='The name of the lab (or Self, Home, etc.)',
        blank=True,
    )
    scanner = models.CharField(max_length=255, blank=True)
    notes_on_development = models.TextField(
        help_text='Chemicals used, development times, techniques, etc.',
        blank=True,
    )
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s added on %s' % (
            self.film, self.created_at.strftime('%Y-%m-%d')
        )

    @property
    def effective_iso(self):
        "Calculates the effective ISO for a pushed or pulled roll."

        # Using a dictionary as a case/switch statement.
        return {
            '': self.film.iso,
            '-2': int(self.film.iso * .25),
            '-1': int(self.film.iso * .5),
            '+1': self.film.iso * 2,
            '+2': self.film.iso * 4,
            '+3': self.film.iso * 8,
        }[self.push_pull]

    def save(self, *args, **kwargs):
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
            sequence = Roll.objects\
                .filter(film__type=self.film.type)\
                .filter(film__format=self.film.format)\
                .filter(started_on__year=self.started_on.year)\
                .filter(owner=self.owner)\
                .count() + 1

            format = '35' if self.film.format == '135' else self.film.format

            # TODO: Check for proper validation of the code field somehow?

            self.code = '%s-%s-%d' % (format, self.film.type, sequence)
            self.status = status_number('loaded')

        # If we've changed our minds and put something back into storage, set
        # everything back to factory condition.

        if self.code and self.status == status_number('storage'):
            # Unload camera
            if self.camera:
                self.camera.status = 'empty'
                self.camera.save()
                self.camera = None

            self.code = ''
            self.push_pull = ''
            self.started_on = None
            self.ended_on = None

        super().save(*args, **kwargs)


class Journal(models.Model):
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    notes = models.TextField(blank=True)
    frame = models.IntegerField(help_text='Last frame of the day')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'journal entry'
        verbose_name_plural = 'journal entries'
        unique_together = (('roll', 'date'),)
        ordering = ['date']

    def __str__(self):
        return 'Journal entry for %s on %s' % (
            self.roll.code, self.date.strftime('%Y-%m-%d')
        )
