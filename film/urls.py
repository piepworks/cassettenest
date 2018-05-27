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
    path('film/type/<type>/', views.film_type, name='film-type'),
    path('film/format/<format>/', views.film_format, name='film-format'),
    path('film/<slug:slug>/', views.film_rolls, name='film-rolls'),
    path('film/<slug:slug>/<int:pk>/',
         views.RollDetailView.as_view(
            template_name='inventory/film_roll_detail.html'
         ), name='film-roll-detail'),
    path('camera/add', views.add_camera, name='add-camera'),
    path('camera/<int:pk>/', views.camera_detail, name='camera-detail'),
    path('camera/<int:pk>/load/', views.load_camera, name='camera-load'),
    path('camera/<int:pk>/edit/', views.edit_camera, name='camera-edit'),
]
