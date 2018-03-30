from django.contrib import admin
from .models import *


class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at',)
    prepopulated_fields = {'slug': ('name',)}


class FilmNameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'speed',)
    prepopulated_fields = {'slug': ('name', 'format',)}


class FilmAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')


admin.site.register(Film, FilmAdmin)
admin.site.register(FilmName, FilmNameAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera)
