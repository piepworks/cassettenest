from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.db.models import Count
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
        latest_roll_list = Roll.objects.filter(owner=owner)\
            .order_by('-created_at')[:5]
        latest_finished_rolls = Roll.objects.filter(
            owner=owner, status=status_number('shot')
        ).order_by('-ended_on')[:5]
        empty_camera_list = Camera.objects\
            .filter(owner=owner, status='empty')
        loaded_roll_list = Roll.objects.filter(
            owner=owner,
            status=status_number('loaded')
        )
        ready_roll_list = Roll.objects.filter(
            owner=owner, status=status_number('shot')
        )
        context = {
            'films': films,
            'latest_roll_list': latest_roll_list,
            'latest_finished_rolls': latest_finished_rolls,
            'empty_camera_list': empty_camera_list,
            'loaded_roll_list': loaded_roll_list,
            'ready_roll_list': ready_roll_list,
        }
        return render(request, 'inventory/index.html', context)
    else:
        return render(request, 'inventory/landing.html')


@login_required
def profile(request):
    owner = request.user
    film_counts = Film.objects\
        .filter(roll__owner=owner, roll__status=status_number('storage'))\
        .annotate(count=Count('roll'))
    format_counts = Film.objects\
        .filter(roll__owner=owner, roll__status=status_number('storage'))\
        .values('format')\
        .annotate(count=Count('format')).distinct().order_by('format')
    projects = Project.objects.filter(owner=owner).order_by('-status')

    # Get the display name of formats choices.
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = \
            force_text(format_choices[format['format']], strings_only=True)

    type_counts = Film.objects\
        .filter(roll__owner=owner, roll__status=status_number('storage'))\
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
    statuses = (
        'loaded',
        'shot',
        'processing',
        'processed',
        'scanned',
        'archived',
    )
    rolls = Roll.objects.filter(owner=owner)\
        .exclude(status=status_number('storage'))\
        .order_by('status')

    if request.GET.get('status') and request.GET.get('status') in statuses:
        status = request.GET.get('status')
        rolls = rolls.filter(status=status_number(status))

    context = {
        'owner': owner,
        'rolls': rolls,
        'status': status,
    }

    return render(request, 'inventory/logbook.html', context)


@login_required
def ready(request):
    owner = request.user
    rolls = Roll.objects.filter(owner=owner, status=status_number('shot'))
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
    statuses = (
        'processing',
        'processed',
        'scanned',
        'archived',
    )
    rolls = Roll.objects.filter(owner=owner)\
        .exclude(status=status_number('storage'))\
        .exclude(status=status_number('shot'))
    rolls_processing = rolls.filter(status=status_number('processing')).count()
    rolls_processed = rolls.filter(status=status_number('processed')).count()
    rolls_scanned = rolls.filter(status=status_number('scanned')).count()
    rolls_archived = rolls.filter(status=status_number('archived')).count()

    if request.method == 'POST':
        current_status = request.POST.get('current_status', '')
        updated_status = request.POST.get('updated_status', '')

        if current_status in statuses and updated_status in statuses:
            rolls.filter(status=status_number(current_status))\
                .update(status=status_number(updated_status))
            messages.success(request, 'Rolls updated!')

        return redirect(reverse('dashboard'))

    context = {
        'rolls': rolls,
        'rolls_processing': rolls_processing,
        'rolls_processed': rolls_processed,
        'rolls_scanned': rolls_scanned,
        'rolls_archived': rolls_archived,
    }

    return render(request, 'inventory/dashboard.html', context)


@require_POST
@login_required
def roll_update(request):
    '''
    Update status (and other things?) for selected rolls in a grid.
    '''
    # I need to make the naming of the rest of the views consistent with this
    # one. Having "film" in the name for things having to do with Rolls isn't
    # right.
    owner = request.user
    # Put these statuses in utility function?
    statuses = (
        'loaded',
        'shot',
        'processing',
        'processed',
        'scanned',
        'archived',
    )
    updated_status = request.POST.get('updated_status')
    rolls = request.POST.getlist('roll')
    lab = request.POST.get('lab', '')
    scanner = request.POST.get('scanner', '')
    notes_on_development = request.POST.get('notes_on_development', '')

    if updated_status in statuses:
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

        # Move this to utilities.
        if roll_count != 1:
            plural = 's'
        else:
            plural = ''

        messages.success(
            request,
            'Status updated on %s selected roll%s!' % (roll_count, plural)
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

        if roll_count > 1:
            plural = 's'
        else:
            plural = ''

        messages.success(
            request,
            'Project deleted and %s roll%s now available for other projects.' %
            (roll_count, plural)
        )
        return redirect(reverse('profile'))
    else:
        return redirect(reverse('project-detail', args=(project.id,)))


@login_required
def project_detail(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)
    iso = iso_variables(request)

    # rolls already in this project
    total_film_count = Film.objects\
        .filter(roll__owner=owner, roll__project=project)
    film_counts = total_film_count\
        .annotate(count=Count('roll'))\
        .order_by('type', 'manufacturer__name', 'name',)

    # rolls available to be added to a project
    film_available_count = Film.objects\
        .filter(
            roll__owner=owner,
            roll__project=None,
            roll__status=status_number('storage'),
        )\
        .annotate(count=Count('roll'))\
        .order_by('type', 'manufacturer__name', 'name',)

    film_available_count = iso_filter(iso, film_available_count)

    context = {
        'owner': owner,
        'project': project,
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'film_available_count': film_available_count,
        'iso_range': iso['range'],
        'iso_value': iso['value'],
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

            if quantity > 1:
                plural = 's'
            else:
                plural = ''

            messages.success(
                request,
                '%s roll%s of %s added!' % (quantity, plural, film)
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

        Roll.objects.filter(owner=owner, film=film, project=project)\
            .update(project=None)
        messages.success(
            request,
            'Removed %s from this project!' % (film)
        )

    return redirect(reverse('project-detail', args=(project.id,)))


@login_required
def film_roll_add(request):
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

            if quantity > 1:
                plural = 's'
            else:
                plural = ''
            messages.success(
                request,
                'Added %s roll%s of %s!' % (quantity, plural, film)
            )
        else:
            messages.error(request, 'Enter a quantity of 1 or more.')

        return redirect(reverse('index'))


@require_POST
@login_required
def film_roll_update(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, id=pk, owner=owner)

    if 'project' in resolve(request.path).url_name:
        form = RollProjectForm(request.POST, instance=roll)
        if form.is_valid():
            roll.project = form.cleaned_data['project']
            roll.save()
            messages.success(request, 'Project updated!')
    else:
        form = RollStatusForm(request.POST, instance=roll)
        if form.is_valid():
            roll.status = form.cleaned_data['status']
            roll.save()
            messages.success(request, 'Status updated!')

    return redirect(
        reverse('film-roll-detail', args=(roll.film.slug, roll.id,))
    )


@login_required
def film_rolls(request, slug):
    '''All the rolls of a particular film that someone has available.'''
    owner = request.user
    rolls = Roll.objects\
        .filter(owner=owner, status=status_number('storage'))\
        .filter(film__slug=slug)
    name = Film.objects.only('name').get(slug=slug)
    context = {
        'rolls': rolls,
        'name': name,
        'owner': owner,
    }

    return render(request, 'inventory/film_rolls.html', context)


@login_required
def film_format(request, format):
    '''All the rolls in a particular format that someone has available.'''
    owner = request.user
    film_counts = Film.objects\
        .filter(roll__owner=owner, roll__status=status_number('storage'))\
        .filter(format=format)\
        .annotate(count=Count('roll'))
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    context = {
        'format': force_text(format_choices[format], strings_only=True),
        'film_counts': film_counts,
        'owner': owner,
    }

    return render(request, 'inventory/film_format.html', context)


@login_required
def film_type(request, type):
    '''All the rolls of a particular film type that someone has available.'''
    owner = request.user
    film_counts = Film.objects\
        .filter(roll__owner=owner, roll__status=status_number('storage'))\
        .filter(type=type)\
        .annotate(count=Count('roll'))
    type_choices = dict(Film._meta.get_field('type').flatchoices)
    context = {
        'type': force_text(type_choices[type], strings_only=True),
        'film_counts': film_counts,
        'owner': owner,
    }

    return render(request, 'inventory/film_type.html', context)


@login_required
def film_roll_detail(request, slug, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)
    statusForm = RollStatusForm(instance=roll)
    projectForm = RollProjectForm(instance=roll)
    projects = Project.objects.filter(owner=owner)
    context = {
        'owner': owner,
        'roll': roll,
        'statusForm': statusForm,
        'projectForm': projectForm,
        'projects': projects,
    }

    return render(request, 'inventory/film_roll_detail.html', context)


@login_required
def film_roll_detail_notes(request, slug, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)

    if request.method == 'POST':
        form = RollNotesForm(request.POST)

        if form.is_valid():
            roll.notes = form.cleaned_data['notes']
            roll.save()

            messages.success(request, 'Notes updated!')

            return redirect(
                reverse('film-roll-detail', args=(roll.film.slug, roll.id,))
            )
    else:
        form = RollNotesForm(instance=roll)
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
def camera_load(request, pk):
    owner = request.user
    current_project = None
    iso = iso_variables(request)

    if request.GET.get('project'):
        try:
            current_project = Project.objects.get(
                pk=request.GET.get('project'),
                owner=owner
            )
        except Project.DoesNotExist:
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
        # The the oldest roll we have of that film in storage.
        if current_project is not None and current_project != 0:
            roll = Roll.objects\
                .filter(
                    owner=owner,
                    film=film,
                    status=status_number('storage'),
                    project=current_project
                )\
                .order_by('created_at')[0]
        else:
            roll = Roll.objects\
                .filter(
                    owner=owner,
                    film=film,
                    status=status_number('storage')
                )\
                .order_by('created_at')[0]
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
        if current_project is not None and current_project != 0:
            film_counts = Film.objects\
                .filter(
                    roll__owner=owner,
                    roll__status=status_number('storage'),
                    roll__project=current_project
                )\
                .filter(format=camera.format)\
                .annotate(count=Count('name'))\
                .order_by('type', 'manufacturer__name', 'name',)
        else:
            film_counts = Film.objects\
                .filter(
                    roll__owner=owner,
                    roll__status=status_number('storage')
                )\
                .filter(format=camera.format)\
                .annotate(count=Count('name'))\
                .order_by('type', 'manufacturer__name', 'name',)

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
            reverse('film-roll-detail', args=(roll.film.slug, roll.id,))
        )
    else:
        roll = ''
        if camera.status == 'loaded':
            roll = Roll.objects.filter(
                camera=camera,
                status=status_number('loaded')
            )[0]

        context = {
            'owner': owner,
            'camera': camera,
            'roll': roll,
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
