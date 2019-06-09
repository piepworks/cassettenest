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
        'project',
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
        'project',
        'created_at',
        'started_on',
        'ended_on',
    )


class CameraAdmin(admin.ModelAdmin):
    list_filter = ('owner',)
    list_display = (
        'owner',
        'name',
        'format',
        'status',
    )


class JournalAdmin(admin.ModelAdmin):
    list_filter = ('roll__owner',)
    list_display = (
        'date',
        'roll_owner',
        'roll',
    )
    date_hierarchy = 'date'
    ordering = ('-date',)

    def roll_owner(self, obj):
        return obj.roll.owner


class ProjectAdmin(admin.ModelAdmin):
    list_filter = (
        'owner',
        'status',
    )
    list_display = (
        'name',
        'owner',
        'created_at',
        'updated_at',
    )


admin.site.register(Film, FilmAdmin)
admin.site.register(Roll, RollAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Journal, JournalAdmin)
