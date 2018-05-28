from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.utils.encoding import force_text
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
import datetime


def index(request):
    if request.user.is_authenticated:
        owner = request.user

        if request.method == 'POST':
            film = get_object_or_404(Film, id=request.POST.get('film', ''))
            quantity = int(request.POST.get('quantity', ''))
            roll = Roll.objects.create(owner=owner, film=film)

            # The first roll has already been created, this creates the rest.
            for x in range(1, quantity):
                roll.pk = None
                roll.save()

            if quantity > 1:
                plural = 's'
            else:
                plural = ''
            messages.success(
                request,
                'Added %s roll%s of %s!' % (quantity, plural, film)
            )

            return HttpResponseRedirect(reverse('index'))

        films = Film.objects.all()
        latest_roll_list = Roll.objects.filter(owner=owner)\
            .order_by('-created_at')[:5]
        latest_finished_rolls = Roll.objects.filter(
            owner=owner, status='shot'
        )[:5]
        empty_camera_list = Camera.objects\
            .filter(owner=owner, status='empty')
        loaded_camera_list = Camera.objects\
            .filter(owner=owner, status='loaded')
        context = {
            'films': films,
            'latest_roll_list': latest_roll_list,
            'latest_finished_rolls': latest_finished_rolls,
            'empty_camera_list': empty_camera_list,
            'loaded_camera_list': loaded_camera_list,
        }

        return render(request, 'inventory/index.html', context)
    else:
        return render(request, 'inventory/landing.html')


@login_required
def profile(request):
    owner = request.user
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


@login_required
def film_rolls(request, slug):
    '''All the rolls of a particular film that someone has available.'''
    owner = request.user
    rolls = Roll.objects\
        .filter(owner=owner, status='storage')\
        .filter(film__slug=slug)
    name = Film.objects.only('name').get(slug=slug)
    context = {
        'rolls': rolls,
        'name': name,
        'owner': owner,
    }

    return render(request, 'inventory/film_rolls.html', context)


class RollDetailView(DetailView):
    model = Roll


@login_required
def film_format(request, format):
    '''All the rolls in a particular format that someone has available.'''
    owner = request.user
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

    return render(request, 'inventory/film_format.html', context)


@login_required
def film_type(request, type):
    '''All the rolls of a particular film type that someone has available.'''
    owner = request.user
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

    return render(request, 'inventory/film_type.html', context)


@login_required
def film_roll_detail_notes(request, slug, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)

    if request.method == 'POST':
        form = RollForm(request.POST)

        if form.is_valid():
            roll.notes = form.cleaned_data['notes']
            roll.save()

            messages.success(request, 'Notes updated!')

            return HttpResponseRedirect(
                reverse('film-roll-detail', args=(roll.film.slug, roll.id,))
            )
    else:
        form = RollForm(instance=roll)

        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
        }

        return render(
            request,
            'inventory/film_roll_detail_notes.html',
            context
        )


@login_required
def load_camera(request, pk):
    owner = request.user
    # Modifying both roll and camera tables
    # Set the camera's status to 'loaded'
    # Set the roll's status to 'loaded'
    # Set the roll's started_on date to today
    # Set the roll's camera to this camera

    if request.method == 'POST':
        camera = get_object_or_404(Camera, id=pk, owner=owner)
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
        messages.success(
            request,
            'Camera loaded with %s %s (code: %s)!' % (
                roll.film.manufacturer,
                roll.film.name,
                roll.code,
            )
        )

        return HttpResponseRedirect(
            reverse('camera-detail', args=(camera.id,))
        )
    else:
        camera = get_object_or_404(Camera, id=pk, owner=owner)
        roll_counts = Film.objects\
            .filter(roll__owner=owner, roll__status='storage')\
            .filter(format=camera.format)\
            .annotate(count=Count('name'))\
            .order_by('type', 'manufacturer__name', 'name',)
        context = {
            'owner': owner,
            'camera': camera,
            'roll_counts': roll_counts,
        }

        return render(request, 'inventory/camera_load.html', context)


@login_required
def camera_detail(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        roll = get_object_or_404(Roll, id=request.POST.get('roll', ''))
        roll.status = 'shot'
        roll.ended_on = datetime.date.today()
        roll.save()
        camera.status = 'empty'
        camera.save()
        messages.success(
            request,
            'Roll of %s %s (code: %s) finished!' % (
                roll.film.manufacturer,
                roll.film.name,
                roll.code,
            )
        )

        return HttpResponseRedirect(
            reverse('film-roll-detail', args=(roll.film.slug, roll.id,))
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

        return render(request, 'inventory/camera_detail.html', context)


@login_required
def add_camera(request):
    owner = request.user

    if request.method == 'POST':
        form = CameraForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            format = form.cleaned_data['format']
            camera = Camera.objects.create(
                owner=owner,
                name=name,
                format=format,
            )

            messages.success(request, 'Camera added!')

            return HttpResponseRedirect(reverse(
                'camera-detail', args=(camera.id,)
            ))
    else:
        form = CameraForm()

        context = {
            'owner': owner,
            'form': form,
        }

        return render(request, 'inventory/camera_add.html', context)


@login_required
def edit_camera(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        form = CameraForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            format = form.cleaned_data['format']
            camera.name = name
            camera.format = format
            camera.save()

            messages.success(request, 'Camera updated!')

            return HttpResponseRedirect(
                reverse('camera-detail', args=(camera.id,))
            )
    else:
        form = CameraForm(instance=camera)

        context = {
            'owner': owner,
            'form': form,
            'camera': camera,
        }

        return render(request, 'inventory/camera_edit.html', context)
