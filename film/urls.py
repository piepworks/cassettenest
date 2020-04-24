from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.urls import include, path
from inventory import views

admin.site.site_header = "Cassette Nest Admin"
admin.site.site_title = "Cassette Nest Admin"
admin.site.index_title = "Cassette Nest’s innards"

urlpatterns = [
    # Users
    path('innards/', admin.site.urls),
    path('register/', views.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Static pages
    path('purpose', views.purpose, name='purpose'),
    path('patterns', views.patterns, name='patterns'),
    path('newsletter', views.newsletter, name='newsletter'),

    # Top-Level
    path('', views.index, name='index'),
    path('logbook/', views.logbook, name='logbook'),
    path('ready/', views.ready, name='ready'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),

    # Rolls
    path('rolls/add/', views.rolls_add, name='rolls-add'),
    path('rolls/update/', views.rolls_update, name='rolls-update'),
    path('roll/add/', views.roll_add, name='roll-add'),
    path('roll/<int:pk>/', views.roll_detail, name='roll-detail'),
    path('roll/<int:pk>/edit/', views.roll_edit, name='roll-edit'),
    path('roll/<int:pk>/delete/', views.roll_delete, name='roll-delete'),

    # Journal Entries for a Roll
    path('roll/<int:roll_pk>/journal/add/',
         views.roll_journal_add, name='roll-journal-add'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/',
         views.roll_journal_detail, name='roll-journal-detail'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/edit/',
         views.roll_journal_edit, name='roll-journal-edit'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/delete/',
         views.roll_journal_delete, name='roll-journal-delete'),

    # Projects
    path('projects/', views.projects, name='projects'),
    path('project/add/', views.project_add, name='project-add'),
    path('project/<int:pk>/edit/', views.project_edit, name='project-edit'),
    path('project/<int:pk>/delete/',
         views.project_delete, name='project-delete'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),
    path('project/<int:pk>/add/',
         views.project_rolls_add, name='project-rolls-add'),
    path('project/<int:pk>/remove/',
         views.project_rolls_remove, name='project-rolls-remove'),
    path('project/<int:pk>/camera/update/',
         views.project_camera_update, name='project-camera-update'),

    # Films
    path('film/', views.inventory, name='inventory'),
    path('film/type/<type>/', views.film_type, name='film-type'),
    path('film/format/<format>/', views.film_format, name='film-format'),
    path('film/<slug:slug>/', views.film_rolls, name='film-rolls'),

    # Cameras and Backs
    path('cameras/', views.cameras, name='cameras'),
    path('camera/add/', views.camera_add, name='camera-add'),
    path('camera/<int:pk>/back/add/',
         views.camera_back_add, name='camera-back-add'),
    path('camera/<int:pk>/',
         views.camera_or_back_detail, name='camera-detail'),
    path('camera/<int:pk>/back/<int:back_pk>/',
         views.camera_or_back_detail, name='camera-back-detail'),
    path('camera/<int:pk>/load/',
         views.camera_or_back_load, name='camera-load'),
    path('camera/<int:pk>/back/<int:back_pk>/load/',
         views.camera_or_back_load, name='camera-back-load'),
    path('camera/<int:pk>/edit/',
         views.camera_edit, name='camera-edit'),
    path('camera/<int:pk>/back/<int:back_pk>/edit/',
         views.camera_back_edit, name='camera-back-edit'),
    path('camera/<int:pk>/delete/',
         views.camera_delete, name='camera-delete'),
    path('camera/<int:pk>/back/<int:back_pk>/delete/',
         views.camera_back_delete, name='camera-back-delete'),

    # Subscribe
    path('subscribe/',
         views.PurchaseSubscriptionView.as_view(),
         name='subscribe'),
    path('subscription-success/<id>',
         views.PurchaseSubscriptionSuccessView.as_view(),
         name='subscription-success'),
    path('subscribe/update_card',
         views.subscription_update_card,
         name='subscription-update-card'),
    path('subscribe/cancel/<id>',
         views.subscription_cancel, name='subscription-cancel'),

    # Sample page that you can’t see without a subscription.
    path('restricted/', views.restricted, name='restricted'),

    # Stripe Webhooks
    path('stripe/', include('djstripe.urls', namespace='djstripe')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
