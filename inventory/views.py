from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.db.models import Count
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.decorators.http import require_POST
from django.utils.encoding import force_text
from django.urls import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *
from .forms import *
from .utils import *
import datetime


def index(request):
    if request.user.is_authenticated:
        owner = request.user
        films = Film.objects.all()
        cameras_empty = Camera.objects.filter(owner=owner, status='empty')
        rolls = Roll.objects.filter(owner=owner)
        rolls_loaded = rolls.filter(status=status_number('loaded'))
        rolls_ready_count = rolls.filter(status=status_number('shot')).count()
        rolls_storage_count = rolls.filter(
            status=status_number('storage')
        ).count()

        projects = Project.objects.filter(
            owner=owner,
            status='current',
        ).order_by('-updated_at',)
        rolls_outstanding_count = rolls.exclude(
            status=status_number('storage')
        ).exclude(
            status=status_number('archived')
        ).count()

        context = {
            'films': films,
            'cameras_empty': cameras_empty,
            'projects': projects,
            'rolls_loaded': rolls_loaded,
            'rolls_ready_count': rolls_ready_count,
            'rolls_storage_count': rolls_storage_count,
            'rolls_outstanding_count': rolls_outstanding_count,
        }
        return render(request, 'inventory/index.html', context)
    else:
        return render(request, 'inventory/landing.html')


@login_required
def profile(request):
    owner = request.user
    # Unused rolls
    total_film_count = Film.objects.filter(
        roll__owner=owner,
        roll__status=status_number('storage'),
    )
    film_counts = total_film_count.annotate(
            count=Count('roll')
        ).order_by(
            'type',
            '-format',
            'manufacturer__name',
            'name',
        )
    format_counts = Film.objects.filter(
            roll__owner=owner,
            roll__status=status_number('storage')
        ).values('format').annotate(
            count=Count('format')
        ).distinct().order_by('format')
    projects = Project.objects.filter(
            owner=owner
        ).order_by(
            '-status',
            '-updated_at',
        )

    # Get the display name of formats choices.
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = force_text(
            format_choices[format['format']],
            strings_only=True
        )

    type_counts = Film.objects.filter(
            roll__owner=owner,
            roll__status=status_number('storage')
        ).values('type').annotate(
            count=Count('type')
        ).distinct().order_by('type')

    # Get the display name of types choices.
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    for type in type_counts:
        type['type_display'] = force_text(
            type_choices[type['type']],
            strings_only=True
        )

    context = {
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'format_counts': format_counts,
        'type_counts': type_counts,
        'projects': projects,
        'owner': owner,
    }

    return render(request, 'inventory/profile.html', context)


@login_required
def logbook(request):
    owner = request.user
    status = 0
    description = ''
    rolls = Roll.objects.filter(owner=owner).exclude(
            status=status_number('storage')
        ).order_by(
            'status',
            '-started_on',
            '-code'
        )

    if request.GET.get('status') and request.GET.get('status') in status_keys:
        status = request.GET.get('status')
        description = status_description(status)
        rolls = rolls.filter(status=status_number(status))

    context = {
        'owner': owner,
        'rolls': rolls,
        'status': status,
        'description': description,
    }

    return render(request, 'inventory/logbook.html', context)


@login_required
def ready(request):
    owner = request.user
    rolls = Roll.objects.filter(
            owner=owner,
            status=status_number('shot')
        ).order_by(
            '-started_on',
            '-code'
        )
    rolls_by_format = rolls.order_by('film__format')
    rolls_by_type = rolls.order_by('film__type')
    rolls_135 = rolls.filter(film__format=135).count()
    rolls_120 = rolls.filter(film__format=120).count()
    rolls_c41 = rolls.filter(film__type='c41').count()
    rolls_c41_135 = rolls.filter(film__type='c41', film__format=135).count()
    rolls_c41_120 = rolls.filter(film__type='c41', film__format=120).count()
    rolls_bw = rolls.filter(film__type='bw').count()
    rolls_bw_135 = rolls.filter(film__type='bw', film__format='135').count()
    rolls_bw_120 = rolls.filter(film__type='bw', film__format='120').count()
    rolls_e6 = rolls.filter(film__type='e6').count()
    rolls_e6_135 = rolls.filter(film__type='e6', film__format='135').count()
    rolls_e6_120 = rolls.filter(film__type='e6', film__format='120').count()

    # Push/Pull C41
    rolls_pull2_c41_135 = rolls.filter(
        film__type='c41', film__format='135', push_pull='-2').count()
    rolls_pull2_c41_120 = rolls.filter(
        film__type='c41', film__format='120', push_pull='-2').count()
    rolls_pull1_c41_135 = rolls.filter(
        film__type='c41', film__format='135', push_pull='-1').count()
    rolls_pull1_c41_120 = rolls.filter(
        film__type='c41', film__format='120', push_pull='-1').count()
    rolls_push1_c41_135 = rolls.filter(
        film__type='c41', film__format='135', push_pull='+1').count()
    rolls_push1_c41_120 = rolls.filter(
        film__type='c41', film__format='120', push_pull='+1').count()
    rolls_push2_c41_135 = rolls.filter(
        film__type='c41', film__format='135', push_pull='+2').count()
    rolls_push2_c41_120 = rolls.filter(
        film__type='c41', film__format='120', push_pull='+2').count()
    rolls_push3_c41_135 = rolls.filter(
        film__type='c41', film__format='135', push_pull='+3').count()
    rolls_push3_c41_120 = rolls.filter(
        film__type='c41', film__format='120', push_pull='+3').count()
    # Push/Pull B&W
    rolls_pull2_bw_135 = rolls.filter(
        film__type='bw', film__format='135', push_pull='-2').count()
    rolls_pull2_bw_120 = rolls.filter(
        film__type='bw', film__format='120', push_pull='-2').count()
    rolls_pull1_bw_135 = rolls.filter(
        film__type='bw', film__format='135', push_pull='-1').count()
    rolls_pull1_bw_120 = rolls.filter(
        film__type='bw', film__format='120', push_pull='-1').count()
    rolls_push1_bw_135 = rolls.filter(
        film__type='bw', film__format='135', push_pull='+1').count()
    rolls_push1_bw_120 = rolls.filter(
        film__type='bw', film__format='120', push_pull='+1').count()
    rolls_push2_bw_135 = rolls.filter(
        film__type='bw', film__format='135', push_pull='+2').count()
    rolls_push2_bw_120 = rolls.filter(
        film__type='bw', film__format='120', push_pull='+2').count()
    rolls_push3_bw_135 = rolls.filter(
        film__type='bw', film__format='135', push_pull='+3').count()
    rolls_push3_bw_120 = rolls.filter(
        film__type='bw', film__format='120', push_pull='+3').count()
    # Push/Pull E6
    rolls_pull2_e6_135 = rolls.filter(
        film__type='e6', film__format='135', push_pull='-2').count()
    rolls_pull2_e6_120 = rolls.filter(
        film__type='e6', film__format='120', push_pull='-2').count()
    rolls_pull1_e6_135 = rolls.filter(
        film__type='e6', film__format='135', push_pull='-1').count()
    rolls_pull1_e6_120 = rolls.filter(
        film__type='e6', film__format='120', push_pull='-1').count()
    rolls_push1_e6_135 = rolls.filter(
        film__type='e6', film__format='135', push_pull='+1').count()
    rolls_push1_e6_120 = rolls.filter(
        film__type='e6', film__format='120', push_pull='+1').count()
    rolls_push2_e6_135 = rolls.filter(
        film__type='e6', film__format='135', push_pull='+2').count()
    rolls_push2_e6_120 = rolls.filter(
        film__type='e6', film__format='120', push_pull='+2').count()
    rolls_push3_e6_135 = rolls.filter(
        film__type='e6', film__format='135', push_pull='+3').count()
    rolls_push3_e6_120 = rolls.filter(
        film__type='e6', film__format='120', push_pull='+3').count()

    context = {
        'owner': owner,
        'rolls': rolls,
        'rolls_by_format': rolls_by_format,
        'rolls_by_type': rolls_by_type,
        'rolls_135': rolls_135,
        'rolls_120': rolls_120,
        'rolls_c41': rolls_c41,
        'rolls_c41_135': rolls_c41_135,
        'rolls_c41_120': rolls_c41_120,
        'rolls_bw': rolls_bw,
        'rolls_bw_135': rolls_bw_135,
        'rolls_bw_120': rolls_bw_120,
        'rolls_e6': rolls_e6,
        'rolls_e6_135': rolls_e6_135,
        'rolls_e6_120': rolls_e6_120,
        # Push/Pull C41
        'rolls_pull2_c41_135': rolls_pull2_c41_135,
        'rolls_pull2_c41_120': rolls_pull2_c41_120,
        'rolls_pull1_c41_135': rolls_pull1_c41_135,
        'rolls_pull1_c41_120': rolls_pull1_c41_120,
        'rolls_push1_c41_135': rolls_push1_c41_135,
        'rolls_push1_c41_120': rolls_push1_c41_120,
        'rolls_push2_c41_135': rolls_push2_c41_135,
        'rolls_push2_c41_120': rolls_push2_c41_120,
        'rolls_push3_c41_135': rolls_push3_c41_135,
        'rolls_push3_c41_120': rolls_push3_c41_120,
        # Push/Pull B&W
        'rolls_pull2_bw_135': rolls_pull2_bw_135,
        'rolls_pull2_bw_120': rolls_pull2_bw_120,
        'rolls_pull1_bw_135': rolls_pull1_bw_135,
        'rolls_pull1_bw_120': rolls_pull1_bw_120,
        'rolls_push1_bw_135': rolls_push1_bw_135,
        'rolls_push1_bw_120': rolls_push1_bw_120,
        'rolls_push2_bw_135': rolls_push2_bw_135,
        'rolls_push2_bw_120': rolls_push2_bw_120,
        'rolls_push3_bw_135': rolls_push3_bw_135,
        'rolls_push3_bw_120': rolls_push3_bw_120,
        # Push/Pull E6
        'rolls_pull2_e6_135': rolls_pull2_e6_135,
        'rolls_pull2_e6_120': rolls_pull2_e6_120,
        'rolls_pull1_e6_135': rolls_pull1_e6_135,
        'rolls_pull1_e6_120': rolls_pull1_e6_120,
        'rolls_push1_e6_135': rolls_push1_e6_135,
        'rolls_push1_e6_120': rolls_push1_e6_120,
        'rolls_push2_e6_135': rolls_push2_e6_135,
        'rolls_push2_e6_120': rolls_push2_e6_120,
        'rolls_push3_e6_135': rolls_push3_e6_135,
        'rolls_push3_e6_120': rolls_push3_e6_120,
    }

    return render(request, 'inventory/ready.html', context)


@login_required
def dashboard(request):
    owner = request.user
    rolls = Roll.objects.filter(
            owner=owner
        ).exclude(
            status=status_number('storage')
        )
    # should 'loaded' be excluded here too?
    rolls_loaded = rolls.filter(status=status_number('loaded')).count()
    rolls_ready = rolls.filter(status=status_number('shot')).count()
    rolls_processing = rolls.filter(status=status_number('processing')).count()
    rolls_processed = rolls.filter(status=status_number('processed')).count()
    rolls_scanned = rolls.filter(status=status_number('scanned')).count()
    rolls_archived = rolls.filter(status=status_number('archived')).count()

    if request.method == 'POST':
        current_status = request.POST.get('current_status', '')
        updated_status = request.POST.get('updated_status', '')

        if current_status in status_keys and updated_status in status_keys:
            rolls.filter(
                    status=status_number(current_status)
                ).update(
                    status=status_number(updated_status)
                )
            messages.success(request, 'Rolls updated!')

        return redirect(reverse('dashboard'))

    context = {
        'rolls': rolls,
        'rolls_loaded': rolls_loaded,
        'rolls_ready': rolls_ready,
        'rolls_processing': rolls_processing,
        'rolls_processed': rolls_processed,
        'rolls_scanned': rolls_scanned,
        'rolls_archived': rolls_archived,
    }

    return render(request, 'inventory/dashboard.html', context)


@require_POST
@login_required
def rolls_update(request):
    '''
    Update status (and other things?) for selected rolls in a grid.
    '''
    # I need to make the naming of the rest of the views consistent with this
    # one. Having "film" in the name for things having to do with Rolls isn't
    # right.
    owner = request.user
    updated_status = request.POST.get('updated_status')
    rolls = request.POST.getlist('roll')
    # Should I be sanitizing the following fields?
    lab = request.POST.get('lab', '')
    scanner = request.POST.get('scanner', '')
    notes_on_development = request.POST.get('notes_on_development', '')

    if updated_status in status_keys:
        # Bulk update selected rows.
        # Verify that the selected row IDs belong to request.user.
        roll_count = 0
        for roll_to_update in rolls:
            roll = Roll.objects.get(pk=roll_to_update)

            if roll.owner == owner:
                roll.status = status_number(updated_status)
                if lab:
                    roll.lab = lab
                if scanner:
                    roll.scanner = scanner
                if notes_on_development:
                    roll.notes_on_development = notes_on_development
                roll.save()
                roll_count += 1

        # Check for errors somehow. Don't assume everything worked.

        messages.success(
            request,
            'Status updated on %s selected %s!' % (
                roll_count,
                pluralize('roll', roll_count)
            )
        )
    else:
        messages.error(request, 'Something is amiss.')

    if request.POST.get('redirect_to') == 'dashboard':
        return redirect(reverse('dashboard'))

    return redirect(reverse('logbook') + '?status=%s' % updated_status)


@login_required
def project_add(request):
    owner = request.user

    if request.method == 'POST':
        form = ProjectForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            notes = form.cleaned_data['notes']
            project = Project.objects.create(
                owner=owner,
                name=name,
                notes=notes,
            )

            messages.success(request, 'Project added!')
            return redirect(reverse('project-detail', args=(project.id,)))
        else:
            messages.error(request, 'You already have that project.')
            return redirect(reverse('project-add'),)
    else:
        form = ProjectForm()
        context = {
            'owner': owner,
            'form': form,
            'action': 'Add',
        }

        return render(request, 'inventory/project_add_edit.html', context)


@login_required
def project_edit(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project.name = form.cleaned_data['name']
            project.notes = form.cleaned_data['notes']
            project.save()
            messages.success(request, 'Project updated!')

            return redirect(reverse('project-detail', args=(project.id,)))
    else:
        form = ProjectForm(instance=project)
        context = {
            'owner': owner,
            'form': form,
            'project': project,
            'action': 'Edit',
        }

        return render(request, 'inventory/project_add_edit.html', context)


@login_required
def project_delete(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)
    rolls = Roll.objects.filter(owner=owner, project=project)
    roll_count = rolls.count()

    if request.method == 'POST':
        rolls.update(project=None)
        project.delete()

        messages.success(
            request,
            'Project deleted and %s %s now available for other projects.' %
            (roll_count, pluralize('roll', roll_count))
        )
        return redirect(reverse('profile'))
    else:
        return redirect(reverse('project-detail', args=(project.id,)))


@login_required
def project_detail(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)
    iso = iso_variables(request)
    # Get all of this user's cameras not already associated with this project.
    cameras = Camera.objects.filter(owner=owner).exclude(
        pk__in=project.cameras.values_list('pk', flat=True)
    )
    loaded_roll_list = Roll.objects.filter(
        owner=owner,
        project=project,
        status=status_number('loaded'),
    )

    # Unused rolls already in this project
    total_film_count = Film.objects.filter(
        roll__owner=owner,
        roll__project=project,
        roll__status=status_number('storage'),
    )
    film_counts = total_film_count.annotate(
            count=Count('roll')
        ).order_by(
            'type',
            '-format',
            'manufacturer__name',
            'name',
        )

    format_counts = {
        '135': film_counts.filter(format='135'),
        '120': film_counts.filter(format='120'),
    }

    # rolls available to be added to a project
    film_available_count = Film.objects.filter(
            roll__owner=owner,
            roll__project=None,
            roll__status=status_number('storage'),
        ).annotate(
            count=Count('roll')
        ).order_by(
            'type',
            'manufacturer__name',
            'name',
        )

    # Filter available films by ISO if set. Return the unaltered list if not.
    film_available_count = iso_filter(iso, film_available_count)

    roll_logbook = Roll.objects.filter(
            owner=owner,
            project=project
        ).exclude(
            status=status_number('storage')
        ).exclude(
            status=status_number('loaded')
        ).order_by(
            'status',
            '-started_on',
            '-code'
        )

    context = {
        'owner': owner,
        'project': project,
        'cameras': cameras,
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'film_available_count': film_available_count,
        'format_counts': format_counts,
        'loaded_roll_list': loaded_roll_list,
        'iso_range': iso['range'],
        'iso_value': iso['value'],
        'roll_logbook': roll_logbook,
    }

    return render(request, 'inventory/project_detail.html', context)


@login_required
def project_rolls_add(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)
    film = get_object_or_404(Film, id=request.POST.get('film', ''))

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', ''))
        available_quantity = Roll.objects.filter(
            owner=owner,
            film=film,
            project=None,
            status=status_number('storage'),
        ).count()

        if quantity <= available_quantity:
            rolls_queryset = Roll.objects.filter(
                owner=owner,
                film=film,
                project=None,
                status=status_number('storage'),
            ).order_by('-created_at')[:quantity]
            Roll.objects.filter(id__in=rolls_queryset).update(project=project)

            messages.success(
                request,
                '%s %s of %s added!' % (
                    quantity,
                    pluralize('roll', quantity),
                    film
                )
            )
        else:
            messages.error(
                request,
                'You don\'t have that many rolls available.'
            )

    return redirect(reverse('project-detail', args=(project.id,)))


@login_required
def project_rolls_remove(request, pk):
    owner = request.user

    if request.method == 'POST':
        project = get_object_or_404(Project, id=pk, owner=owner)
        film = get_object_or_404(Film, id=request.POST.get('film', ''))

        rolls = Roll.objects.filter(
            owner=owner,
            film=film,
            project=project,
            status=status_number('storage'),
        )
        roll_count = rolls.count()
        rolls.update(project=None)

        messages.success(
            request,
            'Removed %s %s of %s from this project!' % (
                roll_count,
                pluralize('roll', roll_count),
                film
            )
        )

    return redirect(reverse('project-detail', args=(project.id,)))


@require_POST
@login_required
def project_camera_update(request, pk):
    '''
    Add or remove a camera from a project.
    '''
    owner = request.user
    actions = ('add', 'remove',)
    project = get_object_or_404(Project, id=pk, owner=owner)
    camera = get_object_or_404(
        Camera,
        id=request.POST.get('camera', ''),
        owner=owner
    )
    action = request.POST.get('action', '')

    if action in actions:
        if action == 'add':
            project.cameras.add(camera)
            messages.success(
                request,
                '%s added to this project!' % camera.name
            )
        if action == 'remove':
            project.cameras.remove(camera)
            messages.success(
                request,
                '%s removed from this project!' % camera.name
            )
    else:
        messages.error(request, 'Something is amiss.')

    return redirect(reverse('project-detail', args=(project.id,)))


@login_required
def rolls_add(request):
    owner = request.user

    if request.method == 'POST':
        film = get_object_or_404(Film, id=request.POST.get('film', ''))

        try:
            quantity = int(request.POST.get('quantity', ''))
        except ValueError:
            messages.error(request, 'Enter a valid quantity.')
            return redirect(reverse('index'))

        if quantity > 0:
            roll = Roll.objects.create(owner=owner, film=film)

            # The first roll has already been created, this creates the rest.
            for x in range(1, quantity):
                roll.pk = None
                roll.save()

            messages.success(
                request,
                'Added %s %s of %s!' % (
                    quantity,
                    pluralize('roll', quantity),
                    film
                )
            )
        else:
            messages.error(request, 'Enter a quantity of 1 or more.')

        return redirect(reverse('index'))


@login_required
def film_rolls(request, slug):
    '''All the rolls of a particular film that someone has or has used.'''
    owner = request.user
    current_project = None
    film = get_object_or_404(Film, slug=slug)
    rolls = Roll.objects.filter(owner=owner, film__slug=slug)
    rolls_storage = rolls.filter(status=status_number('storage'))
    rolls_history = rolls.exclude(
            status=status_number('storage')
        ).order_by(
            '-started_on'
        )

    # Querystring.
    if request.GET.get('project'):
        current_project = get_project_or_none(
            Project,
            owner,
            request.GET.get('project'),
        )
    if current_project is not None and current_project != 0:
        rolls_storage = rolls_storage.filter(project=current_project)
        rolls_history = rolls_history.filter(project=current_project)

    context = {
        'rolls_storage': rolls_storage,
        'rolls_history': rolls_history,
        'film': film,
        'slug': slug,
        'owner': owner,
        'current_project': current_project,
    }

    return render(request, 'inventory/film_rolls.html', context)


@login_required
def film_format(request, format):
    '''All the rolls in a particular format that someone has available.'''
    owner = request.user
    total_film_count = Film.objects.filter(
        roll__owner=owner,
        roll__status=status_number('storage'),
        format=format,
    )
    film_counts = total_film_count.annotate(
            count=Count('roll')
        ).order_by(
            'type',
            'manufacturer__name',
            'name',
        )
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    context = {
        'format': force_text(format_choices[format], strings_only=True),
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'owner': owner,
    }

    return render(request, 'inventory/film_format.html', context)


@login_required
def film_type(request, type):
    '''All the rolls of a particular film type that someone has available.'''
    owner = request.user
    total_film_count = Film.objects.filter(
        roll__owner=owner,
        roll__status=status_number('storage'),
        type=type,
    )
    film_counts = total_film_count.annotate(
            count=Count('roll')
        ).order_by(
            '-format',
            'manufacturer__name',
            'name',
        )
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    context = {
        'type': force_text(type_choices[type], strings_only=True),
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'owner': owner,
    }

    return render(request, 'inventory/film_type.html', context)


@login_required
def roll_detail(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)
    journal_entries = Journal.objects.filter(roll=roll).order_by('date')

    context = {
        'owner': owner,
        'roll': roll,
        'development_statuses': development_statuses,
        'journal_entries': journal_entries
    }

    return render(request, 'inventory/roll_detail.html', context)


@login_required
def roll_edit(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)

    if request.method == 'POST':
        form = RollForm(request.POST)

        if form.is_valid():
            roll.camera = form.cleaned_data['camera']
            roll.lens = form.cleaned_data['lens']
            roll.project = form.cleaned_data['project']
            roll.status = form.cleaned_data['status']
            roll.push_pull = form.cleaned_data['push_pull']
            roll.location = form.cleaned_data['location']
            roll.notes = form.cleaned_data['notes']
            roll.lab = form.cleaned_data['lab']
            roll.scanner = form.cleaned_data['scanner']
            roll.notes_on_development = form.cleaned_data[
                'notes_on_development'
            ]
            roll.save()

            messages.success(request, 'Changes saved!')

            return redirect(
                reverse('roll-detail', args=(roll.id,))
            )
    else:
        form = RollForm(instance=roll)
        form.fields['camera'].queryset = Camera.objects.filter(
            format=roll.film.format,
            owner=owner
        )
        form.fields['project'].queryset = Project.objects.filter(owner=owner)

        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
        }

        return render(
            request,
            'inventory/roll_edit.html',
            context
        )


@require_POST
@login_required
def roll_delete(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)
    film = roll.film

    if roll.camera:
        roll.camera.status = 'empty'
        roll.camera.save()

    roll.delete()

    messages.success(
        request,
        'Roll of %s successfully deleted.' % (film)
    )
    return redirect(reverse('index'))


@login_required
def roll_journal_add(request, roll_pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=roll_pk, owner=owner)

    if request.method == 'POST':
        form = JournalForm(request.POST)

        if form.is_valid():
            date = form.cleaned_data['date']
            notes = form.cleaned_data['notes']
            frame = form.cleaned_data['frame']

            try:
                journal = Journal.objects.create(
                    roll=roll,
                    date=date,
                    notes=notes,
                    frame=frame
                )
                messages.success(request, 'Journal entry added.')
                return redirect(reverse('roll-detail', args=(roll.id,)))
            except IntegrityError:
                messages.error(request, 'Only one entry per date per roll.')
                return redirect(reverse('roll-journal-add', args=(roll.id,)))
        else:
            messages.error(request, 'Something is not right.')
            return redirect(reverse('roll-journal-add', args=(roll.id,)))
    else:
        # Find the last entry's ending frame and add one.
        try:
            starting_frame = Journal.objects.filter(
                roll=roll
            ).reverse()[0].frame + 1
        except IndexError:
            starting_frame = 1

        form = JournalForm(initial={'frame': starting_frame})
        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
        }

        return render(
            request,
            'inventory/roll_journal_add_edit.html',
            context
        )


@login_required
def roll_journal_edit(request, roll_pk, entry_pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=roll_pk, owner=owner)
    entry = get_object_or_404(Journal, roll=roll, pk=entry_pk)

    if request.method == 'POST':
        form = JournalForm(request.POST)

        if form.is_valid():
            entry.date = form.cleaned_data['date']
            entry.notes = form.cleaned_data['notes']
            entry.frame = form.cleaned_data['frame']
            try:
                entry.save()
                messages.success(request, 'Journal entry updated.')
                return redirect(reverse('roll-detail', args=(roll.id,)))
            except IntegrityError:
                messages.error(request, 'Only one entry per date per roll.')
                return redirect(
                    reverse('roll-journal-edit', args=(roll.id, entry.id,))
                )
        else:
            messages.error(request, 'Something is not right.')
            return redirect(
                reverse('roll-journal-edit', args=(roll.id, entry.id,))
            )
    else:
        form = JournalForm(instance=entry)
        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
            'starting_frame': entry.starting_frame,
        }

        return render(
            request,
            'inventory/roll_journal_add_edit.html',
            context
        )


@require_POST
@login_required
def roll_journal_delete(request, roll_pk, entry_pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=roll_pk, owner=owner)
    entry = get_object_or_404(Journal, roll=roll, pk=entry_pk)
    entry_date = entry.date

    entry.delete()

    messages.success(
        request,
        'Journal entry for %s successfully deleted.' % (entry_date)
    )
    return redirect(reverse('roll-detail', args=(roll.id,)))


@login_required
def camera_load(request, pk):
    owner = request.user
    current_project = None

    # Modifying both roll and camera tables
    # Set the camera's status to 'loaded'
    # Set the roll's status to 'loaded'
    # Set the roll's started_on date to today
    # Set the roll's camera to this camera

    if request.method == 'POST':
        camera = get_object_or_404(Camera, id=pk, owner=owner)
        film = get_object_or_404(Film, id=request.POST.get('film', ''))
        push_pull = request.POST.get('push_pull', '')
        rolls = Roll.objects.filter(
                owner=owner,
                film=film,
                film__format=camera.format,
                status=status_number('storage'),
            )

        # Hidden form field
        if request.POST.get('project'):
            current_project = get_project_or_none(
                Project,
                owner,
                request.POST.get('project')
            )

        # The the oldest roll we have of that film in storage.
        if current_project is not None and current_project != 0:
            roll = rolls.filter(
                    project=current_project
                ).order_by('created_at')[0]
        else:
            roll = rolls.order_by('created_at')[0]

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

        return redirect(reverse('camera-detail', args=(camera.id,)))
    else:
        camera = get_object_or_404(Camera, id=pk, owner=owner)
        projects = Project.objects.filter(owner=owner, status='current')
        iso = iso_variables(request)

        # Querystring
        if request.GET.get('project'):
            current_project = get_project_or_none(
                Project,
                owner,
                request.GET.get('project'),
            )

        if current_project is not None and current_project != 0:
            film_counts = Film.objects.filter(
                    roll__owner=owner,
                    roll__status=status_number('storage'),
                    roll__project=current_project
                ).filter(
                    format=camera.format
                ).annotate(
                    count=Count('name')
                ).order_by(
                    'type',
                    'manufacturer__name',
                    'name',
                )
        else:
            film_counts = Film.objects.filter(
                    roll__owner=owner,
                    roll__status=status_number('storage')
                ).filter(
                    format=camera.format
                ).annotate(
                    count=Count('name')
                ).order_by(
                    'type',
                    'manufacturer__name',
                    'name',
                )

        film_counts = iso_filter(iso, film_counts)

        context = {
            'owner': owner,
            'camera': camera,
            'current_project': current_project,
            'projects': projects,
            'film_counts': film_counts,
            'iso_range': iso['range'],
            'iso_value': iso['value'],
        }

        return render(request, 'inventory/camera_load.html', context)


@login_required
def camera_detail(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        roll = get_object_or_404(Roll, id=request.POST.get('roll', ''))
        roll.status = status_number('shot')
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

        return redirect(
            reverse('roll-detail', args=(roll.id,))
        )
    else:
        roll = ''
        rolls_history = Roll.objects.filter(
            owner=owner,
            camera=pk
        ).exclude(
            status=status_number('loaded')
        ).order_by(
            '-started_on'
        )

        if camera.status == 'loaded':
            roll = Roll.objects.filter(
                camera=camera,
                status=status_number('loaded')
            )[0]

        context = {
            'owner': owner,
            'camera': camera,
            'roll': roll,
            'rolls_history': rolls_history,
        }

        return render(request, 'inventory/camera_detail.html', context)


@login_required
def camera_add(request):
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
            return redirect(reverse('camera-detail', args=(camera.id,)))
        else:
            messages.error(request, 'You already have that camera.')
            return redirect(reverse('camera-add'),)
    else:
        form = CameraForm()
        context = {
            'owner': owner,
            'form': form,
        }

        return render(request, 'inventory/camera_add.html', context)


@login_required
def camera_edit(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)

        if form.is_valid():
            name = form.cleaned_data['name']
            format = form.cleaned_data['format']
            camera.name = name
            camera.format = format
            camera.save()

            messages.success(request, 'Camera updated!')
            return redirect(reverse('camera-detail', args=(camera.id,)))
    else:
        form = CameraForm(instance=camera)
        context = {
            'owner': owner,
            'form': form,
            'camera': camera,
        }

        return render(request, 'inventory/camera_edit.html', context)
