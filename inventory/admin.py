from django.contrib import admin
from .models import *


class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at',)
    prepopulated_fields = {'slug': ('name',)}


class FilmAdmin(admin.ModelAdmin):
    list_filter = ('format', 'type', 'iso',)
    list_display = ('__str__', 'type', 'iso',)
    prepopulated_fields = {'slug': ('name', 'format',)}


class RollAdmin(admin.ModelAdmin):
    list_filter = (
        'owner',
        'status',
        'film__format',
        'film__type',
        'film__iso',
    )
    list_display = (
        'film',
        'owner',
        'status',
        'code',
        'push_pull',
        'created_at',
        'started_on',
        'ended_on',
    )


class CameraAdmin(admin.ModelAdmin):
    list_filter = (
        'owner',
    )
    list_display = (
        'owner',
        'name',
        'format',
    )


admin.site.register(Film, FilmAdmin)
admin.site.register(Roll, RollAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(Project)
