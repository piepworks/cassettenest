from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Camera,
    CameraBack,
    Film,
    Journal,
    Manufacturer,
    Profile,
    Project,
    Roll,
)


class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at',)
    prepopulated_fields = {'slug': ('name',)}


class FilmAdmin(admin.ModelAdmin):
    list_filter = ('format', 'type', 'manufacturer', 'iso',)
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


class CameraBackInline(admin.StackedInline):
    model = CameraBack


class CameraAdmin(admin.ModelAdmin):
    inlines = [CameraBackInline]
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


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined',
        'is_staff',
    )
    ordering = ('-date_joined',)


admin.site.register(Film, FilmAdmin)
admin.site.register(Roll, RollAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(CameraBack)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Journal, JournalAdmin)

# Customize the default User admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
