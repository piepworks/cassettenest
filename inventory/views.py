from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.utils.encoding import force_text
from .models import *


def index(request):
    latest_roll_list = Roll.objects.order_by('-created_at')[:5]
    context = {'latest_roll_list': latest_roll_list}
    return render(request, 'inventory/index.html', context)


def profile(request, username):
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects.filter(roll__owner=owner.id).\
        annotate(count=Count('roll'))
    format_counts = Film.objects.filter(roll__owner=owner.id).values('format').\
        annotate(count=Count('format')).distinct().order_by('format')

    # Get the display name of formats choices.
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = force_text(format_choices[format['format']], strings_only=True)

    type_counts = Film.objects.filter(roll__owner=owner.id).values('type').\
        annotate(count=Count('type')).distinct().order_by('type')

    # Get the display name of types choices.
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    for type in type_counts:
        type['type_display'] = force_text(type_choices[type['type']], strings_only=True)

    context = {
        'roll_counts': roll_counts,
        'format_counts': format_counts,
        'type_counts': type_counts,
        'owner': owner,
    }
    return render(request, 'inventory/profile.html', context)


def profile_rolls(request, username, slug):
    owner = get_object_or_404(User, username=username)
    rolls = Roll.objects.filter(owner=owner.id, film__slug=slug)
    name = Film.objects.only('name').get(slug=slug)
    context = {
        'rolls': rolls,
        'name': name,
        'owner': owner,
    }
    return render(request, 'inventory/rolls.html', context)


class RollDetailView(DetailView):
    model = Roll


def profile_format(request, username, format):
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects.filter(roll__owner=owner.id, format=format).\
        annotate(count=Count('roll'))
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    context = {
        'format': force_text(format_choices[format], strings_only=True),
        'roll_counts': roll_counts,
        'owner': owner,
    }
    return render(request, 'inventory/format.html', context)


def profile_type(request, username, type):
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects.filter(roll__owner=owner.id, type=type).\
        annotate(count=Count('roll'))
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    context = {
        'type': force_text(type_choices[type], strings_only=True),
        'roll_counts': roll_counts,
        'owner': owner,
    }
    return render(request, 'inventory/type.html', context)

def load_roll(request, username):
    owner = get_object_or_404(User, username=username)
    cameras = Camera.objects.filter(owner=owner).filter(status='empty')
    context = {
        'owner': owner,
        'cameras': cameras,
    }
    return render(request, 'inventory/load.html', context)
