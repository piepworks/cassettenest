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
    list_display = ('name', 'created_at', 'added_by',)
    list_filter = ('personal', 'added_by',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


class FilmAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'iso', 'created_at', 'added_by',)
    list_filter = ('format', 'type', 'manufacturer', 'iso', 'personal', 'added_by',)
    prepopulated_fields = {'slug': ('name', 'format',)}
    ordering = ('-created_at',)


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


class CameraBackAdmin(admin.ModelAdmin):
    list_filter = ('camera__owner',)
    list_display = (
        'name',
        'camera',
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
        'rolls',
        'cameras',
        'journals',
        'projects',
        'timezone',
        'last_login',
        'date_joined',
    )
    ordering = ('-date_joined',)

    def timezone(self, instance):
        return instance.profile.timezone

    def rolls(self, instance):
        return Roll.objects.filter(owner=instance).count()

    def cameras(self, instance):
        return Camera.objects.filter(owner=instance).count()

    def journals(self, instance):
        return Journal.objects.filter(roll__owner=instance).count()

    def projects(self, instance):
        return Project.objects.filter(owner=instance).count()


admin.site.register(Film, FilmAdmin)
admin.site.register(Roll, RollAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(CameraBack, CameraBackAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Journal, JournalAdmin)

# Customize the default User admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
