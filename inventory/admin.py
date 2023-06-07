from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from .models import (
    Camera,
    CameraBack,
    Stock,
    Film,
    Journal,
    Manufacturer,
    Profile,
    Project,
    Roll,
    Frame,
)
from .utils_paddle import paddle_plan_name
from .forms import FilmForm


class ManufacturerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
        "added_by",
    )
    list_filter = (
        "personal",
        "added_by",
    )
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)


class StockAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = (
        "name",
        "type",
        "iso",
        "added_by",
    )
    list_filter = (
        "manufacturer",
        "type",
        "added_by",
    )


class FilmAdmin(admin.ModelAdmin):
    list_display = (
        "stock",
        "format",
        "created_at",
        "added_by",
    )
    list_filter = (
        "format",
        "stock__manufacturer",
        "personal",
        "added_by",
    )
    ordering = ("-created_at",)

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs["form"] = FilmForm

        return super().get_form(request, obj, **kwargs)


class RollAdmin(admin.ModelAdmin):
    list_filter = (
        "owner",
        "status",
        "project",
        "film__format",
        "film__type",
        "film__iso",
    )
    list_display = (
        "film",
        "owner",
        "status",
        "code",
        "push_pull",
        "project",
        "created_at",
        "started_on",
        "ended_on",
    )


class CameraBackInline(admin.StackedInline):
    model = CameraBack


class CameraAdmin(admin.ModelAdmin):
    inlines = [CameraBackInline]
    list_filter = ("owner",)
    list_display = (
        "owner",
        "name",
        "format",
        "status",
    )


class CameraBackAdmin(admin.ModelAdmin):
    list_filter = ("camera__owner",)
    list_display = (
        "name",
        "camera",
        "format",
        "status",
    )


class JournalAdmin(admin.ModelAdmin):
    list_filter = ("roll__owner",)
    list_display = (
        "date",
        "roll_owner",
        "roll",
    )
    date_hierarchy = "date"
    ordering = ("-date",)

    def roll_owner(self, obj):
        return obj.roll.owner


class ProjectAdmin(admin.ModelAdmin):
    list_filter = (
        "owner",
        "status",
    )
    list_display = (
        "name",
        "owner",
        "created_at",
        "updated_at",
    )


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"
    readonly_fields = ("plan_name",)

    def plan_name(self, instance):
        if instance.paddle_subscription_plan_id:
            return f"{paddle_plan_name(instance.paddle_subscription_plan_id)} = {instance.paddle_subscription_plan_id}"

    plan_name.short_description = "Paddle plan name"
    plan_name.empty_value_display = "None"


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = (
        "username",
        "email",
        "rolls",
        "cameras",
        "is_active",
        "has_active_subscription",
        "subscription_status",
        "timezone",
        "short_last_login",
        "short_date_joined",
    )
    list_filter = (
        "profile__subscription_status",
        "is_active",
    )
    ordering = ("-last_login",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            roll_count=Count("roll", distinct=True),
            camera_count=Count("camera", distinct=True),
            frame_count=Count("roll__frame", distinct=True),
            journal_count=Count("roll__journal", distinct=True),
            project_count=Count("project", distinct=True),
        )
        return qs

    def short_last_login(self, obj):
        if obj:
            return obj.last_login.date().strftime("%Y-%m-%d")

    short_last_login.admin_order_field = "last_login"
    short_last_login.short_description = "Last Login"

    def short_date_joined(self, obj):
        if obj:
            return obj.date_joined.date().strftime("%Y-%m-%d")

    short_date_joined.admin_order_field = "date_joined"
    short_date_joined.short_description = "Date Joined"

    def timezone(self, obj):
        return obj.profile.timezone

    timezone.admin_order_field = "profile__timezone"

    def has_active_subscription(self, obj):
        return obj.profile.has_active_subscription

    has_active_subscription.short_description = "Subscribed"
    has_active_subscription.boolean = True

    def subscription_status(self, obj):
        return obj.profile.subscription_status

    subscription_status.short_description = "Sub status"
    subscription_status.admin_order_field = "profile__subscription_status"

    def rolls(self, obj):
        return obj.roll_count

    rolls.admin_order_field = "roll_count"

    def cameras(self, obj):
        return obj.camera_count

    cameras.admin_order_field = "camera_count"

    def frames(self, obj):
        return obj.frame_count

    frames.admin_order_field = "frame_count"

    def journals(self, obj):
        return obj.journal_count

    journals.admin_order_field = "journal_count"

    def projects(self, obj):
        return obj.project_count

    projects.admin_order_field = "project_count"


class FrameAdmin(admin.ModelAdmin):
    list_filter = ("roll__owner",)
    list_display = (
        "number",
        "roll",
    )


admin.site.register(Stock, StockAdmin)
admin.site.register(Film, FilmAdmin)
admin.site.register(Roll, RollAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Camera, CameraAdmin)
admin.site.register(CameraBack, CameraBackAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Journal, JournalAdmin)
admin.site.register(Frame, FrameAdmin)

# Customize the default User admin.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
