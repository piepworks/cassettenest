from django.db import models
from django.contrib.auth.models import User


class Manufacturer(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    url = models.URLField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s %s in %s' % (
            self.manufacturer, self.name, self.get_format_display()
        )

    class Meta:
        ordering = ['manufacturer__name', 'name']


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

    def __str__(self):
        return '%s\'s %s' % (self.owner, self.name)


class Roll(models.Model):
    STATUS_CHOICES = (
        ('storage', 'Storage'),
        ('loaded', 'Loaded'),
        ('shot', 'Shot'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('scanned', 'Scanned'),
        ('archived', 'Archived'),
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
    code = models.CharField(
        max_length=100,
        help_text='A unique roll code (per year)',
        unique_for_year='started_on',
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='storage',
    )
    push_pull = models.CharField(
        max_length=2,
        choices=PUSH_PULL_CHOICES,
        blank=True,
        verbose_name='Push/Pull',
    )
    notes = models.TextField(blank=True)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

            self.code = '%s-%s-%d' % (format, self.film.type, sequence)
            self.status = 'loaded'

        # Check for proper validation of the code field somehow?

        super().save(*args, **kwargs)

    def __str__(self):
        return '%s added on %s' % (
            self.film, self.created_at.strftime('%Y-%m-%d')
        )
