from django.contrib import admin
from django.urls import include, path, reverse
from django.contrib.auth import views as auth_views
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from inventory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', CreateView.as_view(
        template_name='registration/register.html',
        form_class=UserCreationForm,
        success_url='/'
    ), name='register'),

    # Inventory
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('logbook/', views.logbook, name='logbook'),
    path('ready/', views.ready, name='ready'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('project/add/', views.project_add, name='project-add'),
    path('project/<int:pk>/edit/', views.project_edit, name='project-edit'),
    path('project/<int:pk>/delete/',
         views.project_delete, name='project-delete'),
    path('project/<int:pk>/',
         views.project_detail, name='project-detail'),
    path('project/<int:pk>/add/',
         views.project_rolls_add, name='project-rolls-add'),
    path('project/<int:pk>/remove/',
         views.project_rolls_remove, name='project-rolls-remove'),
    path('film/add/', views.film_roll_add, name='film-roll-add'),
    path('film/update/<int:pk>/',
         views.film_roll_update, name='film-roll-update'),
    path('film/update/<int:pk>/project/',
         views.film_roll_update, name='film-roll-update-project'),
    path('film/type/<type>/', views.film_type, name='film-type'),
    path('film/format/<format>/', views.film_format, name='film-format'),
    path('film/<slug:slug>/', views.film_rolls, name='film-rolls'),
    path('film/<slug:slug>/<int:pk>/',
         views.film_roll_detail, name='film-roll-detail'),
    path('film/<slug:slug>/<int:pk>/notes/',
         views.film_roll_detail_notes, name='film-roll-detail-notes'),
    path('camera/add/', views.camera_add, name='camera-add'),
    path('camera/<int:pk>/', views.camera_detail, name='camera-detail'),
    path('camera/<int:pk>/load/', views.camera_load, name='camera-load'),
    path('camera/<int:pk>/edit/', views.camera_edit, name='camera-edit'),
]
