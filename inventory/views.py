from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.utils.encoding import force_text
from .models import *


def index(request):
    latest_film_list = Film.objects.order_by('-created_at')[:5]
    context = {'latest_film_list': latest_film_list}
    return render(request, 'inventory/index.html', context)


def profile(request, username):
    owner = get_object_or_404(User, username=username)
    film_counts = FilmName.objects.filter(film__owner=owner.id).\
        annotate(count=Count('film'))
    format_counts = FilmName.objects.filter(film__owner=owner.id).values('format').\
        annotate(count=Count('format')).distinct().order_by('format')

    # Get the display name of formats choices.
    format_choices = dict(FilmName._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = force_text(format_choices[format['format']], strings_only=True)

    type_counts = FilmName.objects.filter(film__owner=owner.id).values('type').\
        annotate(count=Count('type')).distinct().order_by('type')

    # Get the display name of types choices.
    type_choices = dict(FilmName._meta.get_field('type').flatchoices)
    for type in type_counts:
        type['type_display'] = force_text(type_choices[type['type']], strings_only=True)

    context = {
        'film_counts': film_counts,
        'format_counts': format_counts,
        'type_counts': type_counts,
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
    film_counts = FilmName.objects.filter(film__owner=owner.id, format=format).\
        annotate(count=Count('film'))
    format_choices = dict(FilmName._meta.get_field('format').flatchoices)
    context = {
        'format': force_text(format_choices[format], strings_only=True),
        'film_counts': film_counts,
        'owner': owner,
    }
    return render(request, 'inventory/format.html', context)


def profile_type(request, username, type):
    owner = get_object_or_404(User, username=username)
    film_counts = FilmName.objects.filter(film__owner=owner.id, type=type).\
        annotate(count=Count('film'))
    type_choices = dict(FilmName._meta.get_field('type').flatchoices)
    context = {
        'type': force_text(type_choices[type], strings_only=True),
        'film_counts': film_counts,
        'owner': owner,
    }
    return render(request, 'inventory/type.html', context)
