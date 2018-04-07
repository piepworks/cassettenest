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
    speed = models.IntegerField()
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='135',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s %s in %s' % (self.manufacturer, self.name, self.get_format_display())

    class Meta:
        ordering = ['name']


class Camera(models.Model):
    """
    A person's camera.
    Not doing a manufacturer field because I want to leave this very freeform.
    Call a camera "Bernice" if you want.
    """

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
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(
        Camera,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='storage',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s added on %s' % (self.film, self.created_at.strftime('%Y-%m-%d'))
