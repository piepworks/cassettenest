from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
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
        'has_active_subscription',
        'subscription_will_cancel',
        'subscription',
        'subscription_status',
        'timezone',
        'last_login',
        'date_joined',
    )
    ordering = ('-date_joined',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            roll_count=Count('roll', distinct=True),
            camera_count=Count('camera', distinct=True),
            journal_count=Count('roll__journal', distinct=True),
            project_count=Count('project', distinct=True),
        )
        return qs

    def timezone(self, obj):
        return obj.profile.timezone

    def has_active_subscription(self, obj):
        return obj.profile.has_active_subscription
    has_active_subscription.short_description = 'Active'
    has_active_subscription.boolean = True

    def subscription(self, obj):
        return obj.profile.subscription
    subscription.short_description = 'Plan'

    def subscription_status(self, obj):
        return obj.profile.subscription_status
    subscription_status.short_description = 'Status'

    def subscription_will_cancel(self, obj):
        return obj.profile.subscription_will_cancel
    subscription_will_cancel.short_description = 'Will Cancel'

    def rolls(self, obj):
        return obj.roll_count

    def cameras(self, obj):
        return obj.camera_count

    def journals(self, obj):
        return obj.journal_count

    def projects(self, obj):
        return obj.project_count

    rolls.admin_order_field = 'roll_count'
    cameras.admin_order_field = 'camera_count'
    journals.admin_order_field = 'journal_count'
    projects.admin_order_field = 'project_count'
    timezone.admin_order_field = 'profile__timezone'


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
