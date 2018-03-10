from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<username>/', views.profile, name='profile'),
    path('<username>/<slug:slug>/', views.profile_films, name='profile-films'),
    path('<username>/<slug:slug>/<int:pk>/',
        views.FilmDetailView.as_view(), name='profile-film'),
]
