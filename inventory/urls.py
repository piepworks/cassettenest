from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<username>/', views.profile, name='profile'),
    path('<username>/type/<type>/',
        views.profile_type, name='profile-type'),
    path('<username>/format/<format>/',
        views.profile_format, name='profile-format'),
    path('<username>/film/<slug:slug>/', views.profile_rolls, name='profile-rolls'),
    path('<username>/film/<slug:slug>/<int:pk>/',
        views.RollDetailView.as_view(), name='profile-roll'),
    path('<username>/load/', views.load_roll, name='load-roll'),
]
