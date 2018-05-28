from django.contrib import admin
from django.urls import include, path, reverse
from django.contrib.auth import views as auth_views
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from inventory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('register/', CreateView.as_view(
        template_name='registration/register.html',
        form_class=UserCreationForm,
        success_url='/'
    ), name='register'),

    # Inventory
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('film/add/', views.film_add, name='film-add'),
    path('film/type/<type>/', views.film_type, name='film-type'),
    path('film/format/<format>/', views.film_format, name='film-format'),
    path('film/<slug:slug>/', views.film_rolls, name='film-rolls'),
    path('film/<slug:slug>/<int:pk>/',
         views.RollDetailView.as_view(
            template_name='inventory/film_roll_detail.html'
         ), name='film-roll-detail'),
    path('film/<slug:slug>/<int:pk>/notes/',
         views.film_roll_detail_notes,
         name='film-roll-detail-notes'),
    path('camera/add/', views.camera_add, name='camera-add'),
    path('camera/<int:pk>/', views.camera_detail, name='camera-detail'),
    path('camera/<int:pk>/load/', views.camera_load, name='camera-load'),
    path('camera/<int:pk>/edit/', views.camera_edit, name='camera-edit'),
]
