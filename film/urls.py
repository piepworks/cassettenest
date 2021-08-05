from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
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

    # Since browsers always ask for /favicon.ico, give it ’em.
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('img/favicon.ico'))),

    # Redirect an authenticated user from the login page.
    path('accounts/login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Static pages
    path('patterns', views.patterns, name='patterns'),

    # Top-Level
    path('', views.index, name='index'),
    path('logbook/', views.logbook, name='logbook'),
    path('ready/', views.ready, name='ready'),
    path('settings/', views.settings, name='settings'),

    # Rolls
    path('rolls/add/', views.rolls_add, name='rolls-add'),
    path('rolls/update/', views.rolls_update, name='rolls-update'),
    path('roll/add/', views.roll_add, name='roll-add'),
    path('roll/<int:pk>/', views.roll_detail, name='roll-detail'),
    path('roll/<int:pk>/edit/', views.roll_edit, name='roll-edit'),
    path('roll/<int:pk>/delete/', views.roll_delete, name='roll-delete'),

    # Journal Entries for a Roll
    path('roll/<int:roll_pk>/journal/add/', views.roll_journal_add, name='roll-journal-add'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/', views.roll_journal_detail, name='roll-journal-detail'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/edit/', views.roll_journal_edit, name='roll-journal-edit'),
    path('roll/<int:roll_pk>/journal/<int:entry_pk>/delete/', views.roll_journal_delete, name='roll-journal-delete'),

    # Frames for a Roll
    path('roll/<int:roll_pk>/frame/add/', views.roll_frame_add, name='roll-frame-add'),
    path('roll/<int:roll_pk>/frame/<int:number>/', views.roll_frame_detail, name='roll-frame-detail'),
    path('roll/<int:roll_pk>/frame/<int:number>/edit/', views.roll_frame_edit, name='roll-frame-edit'),
    path('roll/<int:roll_pk>/frame/<int:number>/delete/', views.roll_frame_delete, name='roll-frame-delete'),

    # Projects
    path('projects/', views.projects, name='projects'),
    path('project/add/', views.project_add, name='project-add'),
    path('project/<int:pk>/edit/', views.project_edit, name='project-edit'),
    path('project/<int:pk>/delete/', views.project_delete, name='project-delete'),
    path('project/<int:pk>/', views.project_detail, name='project-detail'),
    path('project/<int:pk>/add/', views.project_rolls_add, name='project-rolls-add'),
    path('project/<int:pk>/remove/', views.project_rolls_remove, name='project-rolls-remove'),
    path('project/<int:pk>/camera/update/', views.project_camera_update, name='project-camera-update'),

    # Stocks
    path('stocks/', views.stocks, name='stocks'),
    path('stocks/<slug:manufacturer>/', views.stocks_manufacturer, name='stocks-manufacturer'),
    path('stocks/ajax/<slug:manufacturer>/<slug:type>', views.stocks_ajax, name='stocks-ajax'),
    path('stock/', RedirectView.as_view(pattern_name='stocks')),
    path('stock/<slug:manufacturer>/<slug:slug>/', views.stock, name='stock'),

    # Films
    path('film/', views.inventory, name='inventory'),
    path('film/ajax/<slug:format>/<slug:type>', views.inventory_ajax, name='inventory-ajax'),
    path('film/add/', views.film_add, name='film-add'),
    path('film/<slug:slug>/', views.film_rolls, name='film-rolls'),

    # Cameras and Backs
    path('cameras/', views.cameras, name='cameras'),
    path('camera/add/', views.camera_add, name='camera-add'),
    path('camera/<int:pk>/back/add/', views.camera_back_add, name='camera-back-add'),
    path('camera/<int:pk>/', views.camera_or_back_detail, name='camera-detail'),
    path('camera/<int:pk>/back/<int:back_pk>/', views.camera_or_back_detail, name='camera-back-detail'),
    path('camera/<int:pk>/load/', views.camera_or_back_load, name='camera-load'),
    path('camera/<int:pk>/back/<int:back_pk>/load/', views.camera_or_back_load, name='camera-back-load'),
    path('camera/<int:pk>/edit/', views.camera_edit, name='camera-edit'),
    path('camera/<int:pk>/back/<int:back_pk>/edit/', views.camera_back_edit, name='camera-back-edit'),
    path('camera/<int:pk>/delete/', views.camera_delete, name='camera-delete'),
    path('camera/<int:pk>/back/<int:back_pk>/delete/', views.camera_back_delete, name='camera-back-delete'),

    # Export
    path('export/cameras', views.ExportCamerasView.as_view(), name='export-cameras'),
    path('export/camera-backs', views.ExportCameraBacksView.as_view(), name='export-camera-backs'),
    path('export/rolls', views.ExportRollsView.as_view(), name='export-rolls'),
    path('export/projects', views.ExportProjectsView.as_view(), name='export-projects'),
    path('export/journals', views.ExportJournalsView.as_view(), name='export-journals'),

    # Import
    path('import/cameras', views.ImportCamerasView.as_view(), name='import-cameras'),
    path('import/camera-backs', views.ImportCameraBacksView.as_view(), name='import-camera-backs'),
    path('import/rolls', views.ImportRollsView.as_view(), name='import-rolls'),
    path('import/projects', views.ImportProjectsView.as_view(), name='import-projects'),
    path('import/journals', views.ImportJournalsView.as_view(), name='import-journals'),

    # Paddle
    path('paddle-webhooks', views.paddle_webhooks, name='paddle-webhooks'),
    path('subscription-update', views.subscription_update, name='subscription-update'),
    path('subscription-created', views.subscription_created, name='subscription-created'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
