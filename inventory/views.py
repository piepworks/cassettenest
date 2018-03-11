from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from .models import *


def index(request):
    latest_film_list = Film.objects.order_by('-created_at')[:5]
    context = {'latest_film_list': latest_film_list}
    return render(request, 'inventory/index.html', context)


def profile(request, username):
    owner = get_object_or_404(User, username=username)
    film_counts = FilmName.objects.filter(film__owner=owner.id).annotate(count=Count('film'))
    context = {
        'film_counts': film_counts,
        'owner': owner,
    }
    return render(request, 'inventory/profile.html', context)


def profile_films(request, username, slug):
    owner = get_object_or_404(User, username=username)
    films = Film.objects.filter(owner=owner.id, name__slug=slug)
    name = FilmName.objects.only('name').get(slug=slug)
    context = {
        'films': films,
        'name': name,
        'owner': owner,
    }
    return render(request, 'inventory/films.html', context)


class FilmDetailView(DetailView):
    model = Film


def profile_format(request, username, format):
    owner = get_object_or_404(User, username=username)
    films = Film.objects.filter(owner=owner.id, name__format=format)
    context = {
        'films': films,
        'owner': owner,
    }
    return render(request, 'inventory/format.html', context)


def profile_type(request, username, type):
    owner = get_object_or_404(User, username=username)
    films = Film.objects.filter(owner=owner.id, name__type=type)
    context = {
        'films': films,
        'owner': owner,
    }
    return render(request, 'inventory/type.html', context)
