from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.utils.encoding import force_text
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
import datetime


def index(request):
    if request.user.is_authenticated:
        owner = request.user
        latest_roll_list = Roll.objects.filter(owner=owner)\
            .order_by('-created_at')[:5]
        empty_camera_list = Camera.objects\
            .filter(owner=owner, status='empty')
        loaded_camera_list = Camera.objects\
            .filter(owner=owner, status='loaded')
        context = {
            'latest_roll_list': latest_roll_list,
            'empty_camera_list': empty_camera_list,
            'loaded_camera_list': loaded_camera_list,
        }

        return render(request, 'inventory/index.html', context)
    else:
        latest_roll_list = Roll.objects.order_by('-created_at')[:5]
        context = {'latest_roll_list': latest_roll_list}

        return render(request, 'inventory/index_anonymous.html', context)


def profile(request, username):
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects\
        .filter(roll__owner=owner, roll__status='storage')\
        .annotate(count=Count('roll'))
    format_counts = Film.objects\
        .filter(roll__owner=owner, roll__status='storage')\
        .values('format')\
        .annotate(count=Count('format')).distinct().order_by('format')

    # Get the display name of formats choices.
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = \
            force_text(format_choices[format['format']], strings_only=True)

    type_counts = Film.objects\
        .filter(roll__owner=owner, roll__status='storage')\
        .values('type')\
        .annotate(count=Count('type'))\
        .distinct()\
        .order_by('type')

    # Get the display name of types choices.
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    for type in type_counts:
        type['type_display'] = \
            force_text(type_choices[type['type']], strings_only=True)

    context = {
        'roll_counts': roll_counts,
        'format_counts': format_counts,
        'type_counts': type_counts,
        'owner': owner,
    }

    return render(request, 'inventory/profile.html', context)


def profile_rolls(request, username, slug):
    '''All the rolls of a particular film that someone has available.'''
    owner = get_object_or_404(User, username=username)
    rolls = Roll.objects\
        .filter(owner=owner, status='storage')\
        .filter(film__slug=slug)
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
    '''All the rolls in a particular format that someone has available.'''
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects\
        .filter(roll__owner=owner, roll__status='storage')\
        .filter(format=format)\
        .annotate(count=Count('roll'))
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    context = {
        'format': force_text(format_choices[format], strings_only=True),
        'roll_counts': roll_counts,
        'owner': owner,
    }

    return render(request, 'inventory/format.html', context)


def profile_type(request, username, type):
    '''All the rolls of a particular film type that someone has available.'''
    owner = get_object_or_404(User, username=username)
    roll_counts = Film.objects\
        .filter(roll__owner=owner, roll__status='storage')\
        .filter(type=type)\
        .annotate(count=Count('roll'))
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    context = {
        'type': force_text(type_choices[type], strings_only=True),
        'roll_counts': roll_counts,
        'owner': owner,
    }

    return render(request, 'inventory/type.html', context)


def load_cameras(request, username):
    owner = get_object_or_404(User, username=username)
    cameras = Camera.objects.filter(owner=owner).filter(status='empty')
    context = {
        'owner': owner,
        'cameras': cameras,
    }

    return render(request, 'inventory/load.html', context)


@login_required
def load_camera(request, username, pk):
    # Modifying both roll and camera tables
    # Set the camera's status to 'loaded'
    # Set the roll's status to 'loaded'
    # Set the roll's started_on date to today
    # Set the roll's camera to this camera

    if request.method == 'POST':
        # TODO: Check to make sure owner is the currently logged in user.
        owner = get_object_or_404(User, username=username)
        camera = get_object_or_404(Camera, id=pk)

        film = get_object_or_404(Film, id=request.POST.get('film', ''))
        push_pull = request.POST.get('push_pull', '')
        # The the oldest roll we have of that film in storage.
        roll = Roll.objects\
            .filter(owner=owner, film=film, status='storage')\
            .order_by('created_at')[0]
        roll.status = 'loaded'
        roll.camera = camera
        roll.push_pull = push_pull
        roll.started_on = datetime.date.today()
        roll.save()
        camera.status = 'loaded'
        camera.save()

        return HttpResponseRedirect(
            reverse('camera', args=(owner.username, camera.id,))
        )
    else:
        owner = get_object_or_404(User, username=username)
        camera = get_object_or_404(Camera, id=pk)
        roll_counts = Film.objects\
            .filter(roll__owner=owner, roll__status='storage')\
            .filter(format=camera.format)\
            .annotate(count=Count('name'))\
            .order_by('type')
        context = {
            'owner': owner,
            'camera': camera,
            'roll_counts': roll_counts,
        }

        return render(request, 'inventory/load_camera.html', context)


@login_required
def camera(request, username, pk):
    owner = get_object_or_404(User, username=username)
    camera = get_object_or_404(Camera, id=pk)

    if request.method == 'POST':
        # TODO: Check to make sure owner is the currently logged in user.
        roll = get_object_or_404(Roll, id=request.POST.get('roll', ''))
        roll.status = 'shot'
        roll.ended_on = datetime.date.today()
        roll.save()
        camera.status = 'empty'
        camera.save()

        return HttpResponseRedirect(
            reverse('profile-roll', args=(
                owner.username, roll.film.slug, roll.id,
            ))
        )
    else:
        roll = ''
        if camera.status == 'loaded':
            roll = Roll.objects.filter(camera=camera, status='loaded')[0]

        context = {
            'owner': owner,
            'camera': camera,
            'roll': roll,
        }

        return render(request, 'inventory/camera.html', context)
