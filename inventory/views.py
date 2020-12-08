import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, DetailView, FormView
from django.db.models import Count, Q
from django.db import IntegrityError
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_POST
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
import stripe
import djstripe.models
import requests
from djstripe.decorators import subscription_payment_required
from .models import Camera, CameraBack, Film, Manufacturer, Journal, Project, Roll
from .forms import (
    CameraForm,
    CameraBackForm,
    JournalForm,
    PatternsForm,
    ProfileForm,
    ProjectForm,
    PurchaseSubscriptionForm,
    ReadyForm,
    RegisterForm,
    RollForm,
    FilmForm,
    UpdateCardForm,
    UserForm,
    UploadCSVForm,
)
from .utils import (
    development_statuses,
    bulk_status_keys,
    get_project_or_none,
    iso_filter,
    iso_variables,
    pluralize,
    status_description,
    status_keys,
    status_number,
)
from .mixins import ReadCSVMixin, WriteCSVMixin, RedirectAfterImportMixin


@login_required
def index(request):
    owner = request.user
    cameras_total = Camera.objects.filter(owner=owner)
    camera_backs_total = CameraBack.objects.filter(camera__owner=owner)
    cameras_empty = cameras_total.filter(
        status='empty'
    ).exclude(multiple_backs=True)
    camera_backs_empty = camera_backs_total.filter(status='empty')
    rolls = Roll.objects.filter(owner=owner)
    rolls_loaded = rolls.filter(status=status_number('loaded'))
    rolls_ready_count = rolls.filter(status=status_number('shot')).count()
    rolls_storage_count = rolls.filter(
        status=status_number('storage')
    ).count()
    all_projects = Project.objects.filter(
        owner=owner,
    ).order_by('-updated_at',)
    projects_current = all_projects.filter(status='current')
    projects_count = all_projects.count()
    rolls_outstanding_count = rolls.exclude(
        status=status_number('storage')
    ).exclude(
        status=status_number('archived')
    ).count()

    context = {
        'email': owner.email,
        'cameras_total': cameras_total,
        'cameras_empty': cameras_empty,
        'camera_backs_empty': camera_backs_empty,
        'projects_current': projects_current,
        'projects_count': projects_count,
        'rolls': rolls,
        'rolls_loaded': rolls_loaded,
        'rolls_ready_count': rolls_ready_count,
        'rolls_storage_count': rolls_storage_count,
        'rolls_outstanding_count': rolls_outstanding_count,
    }
    return render(request, 'inventory/index.html', context)


def patterns(request):
    roll1 = {
        'film': {
            'type': 'e6',
            'iso': 400
        }
    }
    roll2 = {
        'push_pull': '+2',
        'get_push_pull_display': 'Push 2 stops',
        'effective_iso': 1600,
        'film': {
            'type': 'c41',
            'iso': 400
        }
    }
    roll3 = {
        'push_pull': '-1',
        'get_push_pull_display': 'Pull 1 stop',
        'effective_iso': 50,
        'film': {
            'type': 'bw',
            'iso': 100
        }
    }

    context = {
        'form': PatternsForm,
        'roll1': roll1,
        'roll2': roll2,
        'roll3': roll3,
    }

    return render(request, 'patterns.html', context)


@login_required
def settings(request):
    owner = request.user

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=owner)
        profile_form = ProfileForm(request.POST, instance=owner)

        if user_form.is_valid() and profile_form.is_valid():
            user = owner
            user.first_name = user_form.cleaned_data['first_name']
            user.last_name = user_form.cleaned_data['last_name']
            user.email = user_form.cleaned_data['email']
            user.profile.timezone = profile_form.cleaned_data['timezone']
            user.save()

            messages.success(request, 'Settings updated!')
            return redirect(reverse('index'))
        else:
            for field in user_form:
                for error in field.errors:
                    messages.add_message(request, messages.ERROR, f'{field.name.capitalize()}: {error}')
            return redirect(reverse('settings'))
    else:
        user_form = UserForm(instance=owner)
        profile_form = ProfileForm(instance=owner.profile)
        stripe_form = UpdateCardForm()
        csv_form = UploadCSVForm()
        subscription = False
        exportable = {
            'cameras': Camera.objects.filter(owner=request.user).count(),
            'camera-backs': CameraBack.objects.filter(camera__owner=request.user).count(),
            'rolls': Roll.objects.filter(owner=request.user).count(),
            'projects': Project.objects.filter(owner=request.user).count(),
            'journals': Journal.objects.filter(roll__owner=request.user).count(),
        }
        exportable_data = True if sum(exportable.values()) else False
        imports = [
            'Cameras',
            'Camera-Backs',
            'Rolls',
            'Projects',
            'Journals',
        ]

        try:
            subscriptions = djstripe.models.Subscription.objects.filter(
                customer__subscriber=owner
            )
            if subscriptions:
                subscription = subscriptions[0]
        except djstripe.models.Subscription.DoesNotExist:
            pass

        try:
            subscriber = djstripe.models.Customer.objects.get(subscriber=owner)
            try:
                payment_method = djstripe.models.Source.objects.get(
                    id=subscriber.default_source.id
                ).source_data
            except AttributeError:
                payment_method = False
        except djstripe.models.Customer.DoesNotExist:
            payment_method = False

        try:
            charges = djstripe.models.Charge.objects.filter(
                customer__subscriber=owner
            ).order_by('-created')[:5]
        except djstripe.models.Charge.DoesNotExist:
            charges = False

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'stripe_form': stripe_form,
            'csv_form': csv_form,
            'subscription': subscription,
            'payment_method': payment_method,
            'exportable': exportable,
            'exportable_data': exportable_data,
            'imports': imports,
            'charges': charges,
            'STRIPE_PUBLIC_KEY': djstripe.settings.STRIPE_PUBLIC_KEY,
            'js_needed': True,
        }

        return render(request, 'inventory/settings.html', context)


@method_decorator(login_required, name='dispatch')
class PurchaseSubscriptionView(FormView):
    '''
    Example view to demonstrate how to use dj-stripe to:
    * create a Customer
    * add a card to the Customer
    * create a Subscription using that card
    '''
    template_name = 'inventory/subscribe.html'
    form_class = PurchaseSubscriptionForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if djstripe.models.Plan.objects.count() == 0:
            raise Exception(
                'No Product Plans in the dj-stripe database - create some in '
                'your stripe account and then '
                'run `./manage.py djstripe_sync_plans_from_stripe` '
                '(or use the dj-stripe webhooks)'
            )

        subscription = False

        try:
            subscriptions = djstripe.models.Subscription.objects.filter(
                customer__subscriber=self.request.user
            )
            if subscriptions:
                subscription = subscriptions[0]
        except djstripe.models.Subscription.DoesNotExist:
            pass

        try:
            subscriber = djstripe.models.Customer.objects.get(
                subscriber=self.request.user
            )
            try:
                payment_method = djstripe.models.Source.objects.get(
                    id=subscriber.default_source.id
                ).source_data
            except AttributeError:
                payment_method = False
        except djstripe.models.Customer.DoesNotExist:
            payment_method = False

        ctx['subscription'] = subscription
        ctx['payment_method'] = payment_method
        ctx['owner'] = self.request.user
        ctx['STRIPE_PUBLIC_KEY'] = djstripe.settings.STRIPE_PUBLIC_KEY
        ctx['js_needed'] = True

        return ctx

    def form_valid(self, form):
        stripe_source = form.cleaned_data['stripe_source']
        plan = form.cleaned_data['plan']
        user = self.request.user

        # Create the Stripe Customer, by default subscriber Model is User,
        # this can be overridden with settings.DJSTRIPE_SUBSCRIBER_MODEL
        customer, created = djstripe.models.Customer.get_or_create(
            subscriber=user
        )

        # Add the source as the customer's default card
        customer.add_card(stripe_source)

        # Using the Stripe API, create a subscription for this customer,
        # using the customer's default payment source
        stripe_subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'plan': plan.id}],
            billing='charge_automatically',
            # tax_percent=15,
            api_key=djstripe.settings.STRIPE_SECRET_KEY,
        )

        # Sync the Stripe API return data to the database,
        # this way we don't need to wait for a webhook-triggered sync
        subscription = djstripe.models.Subscription.sync_from_stripe_data(
            stripe_subscription
        )

        self.request.subscription = subscription

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'subscription-success',
            kwargs={'id': self.request.subscription.id},
        )


@method_decorator(login_required, name='dispatch')
class PurchaseSubscriptionSuccessView(DetailView):
    template_name = 'inventory/subscribe_success.html'

    queryset = djstripe.models.Subscription.objects.all()
    slug_field = 'id'
    slug_url_kwarg = 'id'
    context_object_name = 'subscription'


@require_POST
@login_required
def subscription_update_card(request):
    form = UpdateCardForm(request.POST)

    if form.is_valid():
        customer = djstripe.models.Customer.objects.get(
            subscriber=request.user
        )

        # Delete all existing payment sources
        sources = djstripe.models.Source.objects.filter(customer=customer)
        for source in sources:
            source.detach()

        # Set a new default payment source
        stripe_source = form.cleaned_data['stripe_source']
        customer.add_card(stripe_source)

        messages.error(request, 'Card updated!')
    else:
        messages.error(request, 'Something is not right.')

    return redirect(reverse('settings'),)


@require_POST
@login_required
def subscription_cancel(request, id):
    owner = request.user

    try:
        subscription = djstripe.models.Subscription.objects.get(
            customer__subscriber=owner,
            id=id
        )
        subscription.cancel(at_period_end=True)
    except djstripe.models.Subscription.DoesNotExist:
        # TODO: Display an error
        pass

    return redirect('settings')


@login_required
@subscription_payment_required
def restricted(request):
    '''
    An example page that you must have a subscription to view.
    '''

    context = {}

    return render(request, 'inventory/restricted.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()

            # Automatically log in
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)

            # Send Trey an email about this.
            email = form.cleaned_data.get('email')
            send_mail(
                subject='New Cassette Nest user!',
                message=f'{username} / {email} just signed up!',
                from_email='trey@cassettenest.com',
                recipient_list=['boss@treylabs.com']
            )

            return redirect('index')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def inventory(request):
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
    }

    return render(request, 'inventory/film.html', context)


@login_required
def logbook(request):
    owner = request.user
    status = 0
    description = ''
    rolls = Roll.objects.filter(owner=owner).exclude(
        status=status_number('storage')
    ).order_by(
        'status',
        '-ended_on',
        '-started_on',
        '-code'
    )
    year = ''
    all_years = {}
    all_years_count = rolls.count()

    for y in rolls.dates('started_on', 'year'):
        count = rolls.filter(started_on__year=y.year).count()
        all_years.update({y.year: count})

    if request.GET.get('status') and request.GET.get('status') in status_keys:
        status = request.GET.get('status')
        if status == 'storage':
            return redirect(reverse('inventory'))
        else:
            description = status_description(status)
            rolls = rolls.filter(status=status_number(status))

    if request.GET.get('year'):
        year = request.GET.get('year')
        rolls = rolls.filter(started_on__year=year)

    # Pagination / 20 per page
    paginator = Paginator(rolls, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'owner': owner,
        'rolls': rolls,
        'status': status,
        'page_obj': page_obj,
        'description': description,
        'year': year,
        'all_years': all_years,
        'all_years_count': all_years_count,
        'bulk_status_keys': bulk_status_keys
    }

    return render(request, 'inventory/logbook.html', context)


@login_required
def ready(request):
    owner = request.user
    form = ReadyForm()
    rolls = Roll.objects.filter(
        owner=owner,
        status=status_number('shot')
    ).order_by(
        '-ended_on',
        '-started_on',
        '-code'
    )

    ready_rolls = {
        'c41': rolls.filter(film__type='c41'),
        'bw': rolls.filter(film__type='bw'),
        'e6': rolls.filter(film__type='e6'),
        '135': {
            'all': rolls.filter(film__format=135),
            'c41': rolls.filter(film__format=135, film__type='c41'),
            'bw': rolls.filter(film__format=135, film__type='bw'),
            'e6': rolls.filter(film__format=135, film__type='e6'),
        },
        '120': {
            'all': rolls.filter(film__format=120),
            'c41': rolls.filter(film__format=120, film__type='c41'),
            'bw': rolls.filter(film__format=120, film__type='bw'),
            'e6': rolls.filter(film__format=120, film__type='e6'),
        }
    }

    ready_counts = {
        'all': rolls.count(),
        '135': ready_rolls['135']['all'].count(),
        '120': ready_rolls['120']['all'].count(),
        'c41': {
            'all': ready_rolls['c41'].count(),
            '135': ready_rolls['135']['c41'].count(),
            '120': ready_rolls['120']['c41'].count(),
            'pull2': {
                '135': ready_rolls['135']['c41'].filter(push_pull='-2').count(),
                '120': ready_rolls['120']['c41'].filter(push_pull='-2').count(),
            },
            'pull1': {
                '135': ready_rolls['135']['c41'].filter(push_pull='-1').count(),
                '120': ready_rolls['120']['c41'].filter(push_pull='-1').count(),
            },
            'push1': {
                '135': ready_rolls['135']['c41'].filter(push_pull='+1').count(),
                '120': ready_rolls['120']['c41'].filter(push_pull='+1').count(),
            },
            'push2': {
                '135': ready_rolls['135']['c41'].filter(push_pull='+2').count(),
                '120': ready_rolls['120']['c41'].filter(push_pull='+2').count(),
            },
            'push3': {
                '135': ready_rolls['135']['c41'].filter(push_pull='+3').count(),
                '120': ready_rolls['120']['c41'].filter(push_pull='+3').count(),
            },
        },
        'bw': {
            'all': ready_rolls['bw'].count(),
            '135': ready_rolls['135']['bw'].count(),
            '120': ready_rolls['120']['bw'].count(),
            'pull2': {
                '135': ready_rolls['135']['bw'].filter(push_pull='-2').count(),
                '120': ready_rolls['120']['bw'].filter(push_pull='-2').count(),
            },
            'pull1': {
                '135': ready_rolls['135']['bw'].filter(push_pull='-1').count(),
                '120': ready_rolls['120']['bw'].filter(push_pull='-1').count(),
            },
            'push1': {
                '135': ready_rolls['135']['bw'].filter(push_pull='+1').count(),
                '120': ready_rolls['120']['bw'].filter(push_pull='+1').count(),
            },
            'push2': {
                '135': ready_rolls['135']['bw'].filter(push_pull='+2').count(),
                '120': ready_rolls['120']['bw'].filter(push_pull='+2').count(),
            },
            'push3': {
                '135': ready_rolls['135']['bw'].filter(push_pull='+3').count(),
                '120': ready_rolls['120']['bw'].filter(push_pull='+3').count(),
            },
        },
        'e6': {
            'all': ready_rolls['e6'].count(),
            '135': ready_rolls['135']['e6'].count(),
            '120': ready_rolls['120']['e6'].count(),
            'pull2': {
                '135': ready_rolls['135']['e6'].filter(push_pull='-2').count(),
                '120': ready_rolls['120']['e6'].filter(push_pull='-2').count(),
            },
            'pull1': {
                '135': ready_rolls['135']['e6'].filter(push_pull='-1').count(),
                '120': ready_rolls['120']['e6'].filter(push_pull='-1').count(),
            },
            'push1': {
                '135': ready_rolls['135']['e6'].filter(push_pull='+1').count(),
                '120': ready_rolls['120']['e6'].filter(push_pull='+1').count(),
            },
            'push2': {
                '135': ready_rolls['135']['e6'].filter(push_pull='+2').count(),
                '120': ready_rolls['120']['e6'].filter(push_pull='+2').count(),
            },
            'push3': {
                '135': ready_rolls['135']['e6'].filter(push_pull='+3').count(),
                '120': ready_rolls['120']['e6'].filter(push_pull='+3').count(),
            },
        },
    }

    # Pagination / 20 per page
    paginator = Paginator(rolls, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'owner': owner,
        'form': form,
        'rolls': ready_counts,
        'page_obj': page_obj,
        'bulk_status_keys': bulk_status_keys
    }

    return render(request, 'inventory/ready.html', context)


@login_required
def dashboard(request):
    owner = request.user
    rolls = Roll.objects.filter(owner=owner)
    rolls_storage = rolls.filter(status=status_number('storage')).count()
    rolls_loaded = rolls.filter(status=status_number('loaded')).count()
    rolls_ready = rolls.filter(status=status_number('shot')).count()
    rolls_processing = rolls.filter(status=status_number('processing')).count()
    rolls_processed = rolls.filter(status=status_number('processed')).count()
    rolls_scanned = rolls.filter(status=status_number('scanned')).count()
    rolls_archived = rolls.filter(status=status_number('archived')).count()

    if request.method == 'POST':
        current_status = request.POST.get('current_status', '')
        updated_status = request.POST.get('updated_status', '')

        if (current_status in bulk_status_keys
                and updated_status in bulk_status_keys):
            rolls_to_update = rolls.filter(
                status=status_number(current_status)
            )
            roll_count = rolls_to_update.count()
            rolls_to_update.update(
                status=status_number(updated_status)
            )
            messages.success(
                request,
                '%s %s updated from %s to %s!' % (
                    roll_count,
                    pluralize('roll', roll_count),
                    current_status,
                    updated_status
                )
            )

        return redirect(reverse('dashboard'))

    context = {
        'rolls': rolls,
        'rolls_storage': rolls_storage,
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
    owner = request.user
    form = ReadyForm(request.POST)
    current_status = request.POST.get('current_status')
    updated_status = request.POST.get('updated_status')
    rolls = request.POST.getlist('roll')

    if form.is_valid():
        # This is for the sake of the Ready page.
        # I guess this works with forms on Logbook views since none of the
        # fields are required so it happily ignores them not being there?
        lab = form.cleaned_data['lab']
        scanner = form.cleaned_data['scanner']
        notes_on_development = form.cleaned_data['notes_on_development']
    else:
        messages.error(request, 'Something is not right.')
        return redirect(reverse('ready'),)

    if updated_status in bulk_status_keys:
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
            '%s %s updated from %s to %s!' % (
                roll_count,
                pluralize('roll', roll_count),
                current_status,
                updated_status
            )
        )
    else:
        messages.error(request, 'Something is amiss.')

    if request.POST.get('redirect_to') == 'dashboard':
        return redirect(reverse('dashboard'))

    return redirect(reverse('logbook') + '?status=%s' % updated_status)


@login_required
def projects(request):
    owner = request.user
    projects = Project.objects.filter(
        owner=owner
    ).order_by(
        '-status',
        '-updated_at',
    )
    context = {
        'projects': projects,
    }

    return render(request, 'inventory/projects.html', context)


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

            if project.status == 'archived':
                rolls = Roll.objects.filter(
                    owner=owner,
                    project=project,
                    status=status_number('storage')
                )
                roll_count = rolls.count()

                if rolls:
                    rolls.update(project=None)

                    messages.success(
                        request,
                        '''
                        Project archived and %s %s now available for other
                        projects.
                        '''
                        % (roll_count, pluralize('roll', roll_count))
                    )
                else:
                    # No unused rolls
                    messages.success(request, 'Project archived!')
            else:
                # Status not changed to 'archived'
                messages.success(request, 'Project updated!')

            return redirect(reverse('project-detail', args=(project.id,)))
    else:
        form = ProjectForm(instance=project)
        context = {
            'owner': owner,
            'form': form,
            'project': project,
            'action': 'Edit',
            'js_needed': True,
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
        return redirect(reverse('projects'))
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
    ).exclude(
        status='unavailable'
    )
    cameras_empty = project.cameras.filter(status='empty')
    loaded_roll_list = Roll.objects.filter(
        owner=owner,
        project=project,
        status=status_number('loaded'),
    )

    rolls_loaded_outside_project = []
    for camera in project.cameras.all():
        for roll in camera.roll_set.all():
            if (
                roll.status == status_number('loaded')
                and roll.project != project
            ):
                rolls_loaded_outside_project.append(roll)

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
    ).order_by(
        'status',
        '-ended_on',
        '-started_on',
        '-code'
    )

    # Pagination / 20 per page
    paginator = Paginator(roll_logbook, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'owner': owner,
        'project': project,
        'cameras': cameras,
        'cameras_empty': cameras_empty,
        'rolls_loaded_outside_project': rolls_loaded_outside_project,
        'total_film_count': total_film_count,
        'film_counts': film_counts,
        'film_available_count': film_available_count,
        'format_counts': format_counts,
        'loaded_roll_list': loaded_roll_list,
        'iso_range': iso['range'],
        'iso_value': iso['value'],
        'roll_logbook': roll_logbook,
        'page_obj': page_obj,
        'js_needed': True,
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
                'You don’t have that many rolls available.'
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
                # https://stackoverflow.com/a/4736172/96257
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

        return redirect(reverse('inventory'))

    else:
        # Exclude films that are flagged as `personal` and not created by the current user.
        films = Film.objects.all().exclude(Q(personal=True) & ~Q(added_by=owner))
        context = {
            'films': films,
            'js_needed': True,
        }

        return render(request, 'inventory/rolls_add.html', context)


@login_required
def roll_add(request):
    '''For adding non-storage rolls.'''
    owner = request.user

    if request.method == 'POST':
        form = RollForm(request.POST)

        if form.is_valid():
            film = get_object_or_404(Film, id=request.POST.get('film', ''))
            status = form.cleaned_data['status']

            roll = Roll.objects.create(owner=owner, film=film)
            # Validate ended on isn't before started on?
            roll.started_on = form.cleaned_data['started_on']
            roll.ended_on = form.cleaned_data['ended_on']
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

            messages.success(
                request,
                'Added a roll: <a href="%s">%s</a>!'
                % (
                    reverse('roll-detail', args=(roll.id,)),
                    roll.code
                ),
                extra_tags='safe'
            )
            # TODO: redirect to year=year for this roll and status=all.
            if 'another' in request.POST:
                return redirect(reverse('roll-add'))
            else:
                return redirect(reverse('logbook') + '?status=' + status[3:])
        else:
            messages.error(request, 'Please fill out the form.')
            return redirect(reverse('roll-add'))

    else:
        films = Film.objects.all()
        form = RollForm()
        form.fields['camera'].queryset = Camera.objects.filter(owner=owner)
        form.fields['project'].queryset = Project.objects.filter(owner=owner)
        status_choices = Roll._meta.get_field('status').flatchoices
        del status_choices[0:2]  # remove storage & loaded
        form.fields['status'].choices = status_choices

        context = {
            'owner': owner,
            'form': form,
            'films': films,
            'js_needed': True,
        }

        return render(request, 'inventory/roll_add.html', context)


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
def film_add(request):
    if request.method == 'POST':
        form = FilmForm(request.POST, user=request.user)
        output = 'error'

        if form.is_valid():
            if form.cleaned_data['new_manufacturer']:
                # Create new manufactuter and get a reference to it.
                new_manufacturer = form.cleaned_data['new_manufacturer']
                try:
                    manufacturer = Manufacturer.objects.create(
                        personal=True,
                        added_by=request.user,
                        name=new_manufacturer,
                        slug=slugify(new_manufacturer),
                    )
                except IntegrityError:
                    messages.error(request, 'There’s already a manufacturer with that name.')
                    context = {
                        'form': form,
                        'js_needed': True,
                    }

                    return render(request, 'inventory/film_add.html', context)
            else:
                manufacturer = form.cleaned_data['manufacturer']

            film = Film.objects.create(
                personal=True,
                added_by=request.user,
                manufacturer=manufacturer,
                name=form.cleaned_data['name'],
                slug=slugify(form.cleaned_data['name']),
                format=form.cleaned_data['format'],
                type=form.cleaned_data['type'],
                iso=form.cleaned_data['iso'],
                url=form.cleaned_data['url'],
                description=form.cleaned_data['description'],
            )
            messages.success(request, f'New film “{film}” added!')

            current_site = get_current_site(request)
            if 'new_manufacturer' in locals():
                message_addendum = f'''“{new_manufacturer}” is a new manufacturer.\n
                    https://{current_site}{reverse('admin:inventory_manufacturer_change', args=(manufacturer.id,))}
                '''
            else:
                message_addendum = ''
            send_mail(
                subject='New film added!',
                message=f'''{request.user} added “{film}.”\n
                    https://{current_site}{reverse('admin:inventory_film_change', args=(film.id,))}\n
                    {message_addendum}
                ''',
                from_email='trey@cassettenest.com',
                recipient_list=['boss@treylabs.com']
            )

            if form.cleaned_data['destination'] != 'add-storage':
                if 'another' in request.POST:
                    return redirect(reverse('film-add') + '?destination=add-logbook')
                else:
                    # Go back to add roll to logbook page.
                    return redirect(reverse('roll-add') + f'?film={film.id}')
            else:
                if 'another' in request.POST:
                    return redirect('film-add')
                else:
                    # Go back to add rolls to storage page.
                    return redirect(reverse('rolls-add') + f'?film={film.id}')
        else:
            context = {
                'form': form,
                'js_needed': True,
            }
    else:
        destination = request.GET.get('destination')
        if destination:
            form = FilmForm(user=request.user, initial={'destination': destination})
        else:
            form = FilmForm(user=request.user, initial={'destination': 'add-storage'})
        context = {
            'form': form,
            'js_needed': True,
        }

    return render(request, 'inventory/film_add.html', context)


@login_required
def roll_detail(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)
    journal_entries = Journal.objects.filter(roll=roll).order_by('date')

    context = {
        'owner': owner,
        'roll': roll,
        'development_statuses': development_statuses,
        'journal_entries': journal_entries,
        'js_needed': True,
    }

    return render(request, 'inventory/roll_detail.html', context)


@login_required
def roll_edit(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)

    if request.method == 'POST':
        form = RollForm(request.POST)

        if form.is_valid():
            roll.started_on = form.cleaned_data['started_on']
            roll.ended_on = form.cleaned_data['ended_on']
            roll.camera = form.cleaned_data['camera']
            roll.code = form.cleaned_data['code']
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

            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
        form = RollForm(instance=roll)
        form.fields['camera'].queryset = Camera.objects.filter(
            format=roll.film.format,
            owner=owner
        )
        form.fields['project'].queryset = Project.objects.filter(owner=owner)

        status_choices = Roll._meta.get_field('status').flatchoices
        del status_choices[1]  # remove loaded
        form.fields['status'].choices = status_choices

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
def roll_journal_detail(request, roll_pk, entry_pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=roll_pk, owner=owner)
    entry = get_object_or_404(Journal, roll=roll, pk=entry_pk)

    context = {
        'roll': roll,
        'entry': entry,
        'js_needed': True,
    }

    return render(
        request,
        'inventory/roll_journal_detail.html',
        context
    )


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
                Journal.objects.create(
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
            'action': 'Add',
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
                return redirect(reverse('roll-journal-detail', args=(roll.id, entry.id)))
            except IntegrityError:
                messages.error(request, 'Only one entry per date per roll.')
                return redirect(
                    reverse('roll-journal-edit', args=(roll.id, entry.id))
                )
        else:
            messages.error(request, 'Something is not right.')
            return redirect(
                reverse('roll-journal-edit', args=(roll.id, entry.id))
            )
    else:
        form = JournalForm(instance=entry)
        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
            'starting_frame': entry.starting_frame,
            'action': 'Edit',
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
def cameras(request):
    owner = request.user
    cameras = Camera.objects.filter(
        owner=owner
    ).order_by(
        '-status',
        '-updated_at',
    )
    context = {
        'cameras': cameras,
    }

    return render(request, 'inventory/cameras.html', context)


@login_required
def camera_or_back_load(request, pk, back_pk=None):
    owner = request.user
    current_project = None
    camera = get_object_or_404(Camera, id=pk, owner=owner)
    if back_pk:
        camera_back = get_object_or_404(
            CameraBack,
            id=back_pk,
            camera__owner=owner
        )
        camera_or_back = camera_back
    else:
        camera_back = None
        camera_or_back = camera

    # Modifying both roll and camera tables
    # Set the camera's status to 'loaded'
    # Set the roll's status to 'loaded'
    # Set the roll's started_on date to today
    # Set the roll's camera to this camera

    if request.method == 'POST':
        film = get_object_or_404(Film, id=request.POST.get('film', ''))
        push_pull = request.POST.get('push_pull', '')
        rolls = Roll.objects.filter(
            owner=owner,
            film=film,
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
        if camera_back:
            roll.camera_back = camera_back
        roll.push_pull = push_pull
        roll.started_on = datetime.date.today()
        roll.save()
        messages.success(
            request,
            '%s loaded with %s %s (code: %s)!' % (
                camera_or_back,
                roll.film.manufacturer,
                roll.film.name,
                roll.code,
            )
        )

        if current_project:
            return redirect(reverse(
                'project-detail', args=(current_project.id,))
            )
        else:
            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
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
            ).annotate(
                count=Count('name')
            ).order_by(
                'type',
                'manufacturer__name',
                'name',
            )
            if camera_or_back.format:
                film_counts = film_counts.filter(format=camera_or_back.format)
        else:
            film_counts = Film.objects.filter(
                roll__owner=owner,
                roll__status=status_number('storage')
            ).annotate(
                count=Count('name')
            ).order_by(
                'type',
                'manufacturer__name',
                'name',
            )
            if camera_or_back.format:
                film_counts = film_counts.filter(format=camera_or_back.format)

        film_counts = iso_filter(iso, film_counts)

        context = {
            'owner': owner,
            'camera': camera,
            'camera_back': camera_back,
            'camera_or_back': camera_or_back,
            'current_project': current_project,
            'projects': projects,
            'film_counts': film_counts,
            'iso_range': iso['range'],
            'iso_value': iso['value'],
        }

        return render(request, 'inventory/camera_or_back_load.html', context)


@login_required
def camera_or_back_detail(request, pk, back_pk=None):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)
    if back_pk:
        camera_back = get_object_or_404(
            CameraBack,
            id=back_pk,
            camera__owner=owner
        )
        camera_or_back = camera_back
    else:
        camera_back = None
        camera_or_back = camera

    if request.method == 'POST':
        roll = get_object_or_404(Roll, id=request.POST.get('roll', ''))
        roll.status = status_number('shot')
        roll.save()
        messages.success(
            request,
            'Roll of %s %s (code: %s) finished!' % (
                roll.film.manufacturer,
                roll.film.name,
                roll.code,
            )
        )

        if roll.project:
            return redirect(reverse('project-detail', args=(roll.project.id,)))
        else:
            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
        roll = ''
        if camera_back:
            rolls_history = ''
        else:
            rolls_history = Roll.objects.filter(
                owner=owner,
                camera=pk
            ).exclude(
                status=status_number('loaded')
            ).order_by(
                '-started_on'
            )

        if camera_back:
            if camera_back.status == 'loaded':
                roll = Roll.objects.filter(
                    camera_back=camera_back,
                    status=status_number('loaded')
                )[0]
        else:
            if camera.status == 'loaded':
                roll = Roll.objects.filter(
                    camera=camera,
                    status=status_number('loaded')
                )[0]

        context = {
            'owner': owner,
            'camera': camera,
            'camera_back': camera_back,
            'camera_or_back': camera_or_back,
            'roll': roll,
            'rolls_history': rolls_history,
        }

        if camera_back:
            return render(
                request, 'inventory/camera_back_detail.html', context
            )
        else:
            return render(
                request, 'inventory/camera_detail.html', context
            )


@login_required
def camera_add(request):
    owner = request.user

    if request.method == 'POST':
        form = CameraForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            format = form.cleaned_data['format']
            notes = form.cleaned_data['notes']
            unavailable = form.cleaned_data['unavailable']
            camera = Camera.objects.create(
                owner=owner,
                name=name,
                format=format,
                notes=notes,
                status='unavailable' if unavailable else 'empty'
            )

            messages.success(request, 'Camera added!')

            if 'another' in request.POST:
                return redirect('camera-add')
            else:
                return redirect(reverse('camera-detail', args=(camera.id,)))
        else:
            # TODO: Output the actual error from the form instead of this
            # hardcoded one.
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
def camera_back_add(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        form = CameraBackForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            notes = form.cleaned_data['notes']
            unavailable = form.cleaned_data['unavailable']
            camera_back = CameraBack.objects.create(
                name=name,
                camera=camera,
                notes=notes,
                status='unavailable' if unavailable else 'empty'
            )

            messages.success(
                request, 'Camera back for %s added!' % (camera.name)
            )

            if 'another' in request.POST:
                return redirect(reverse('camera-back-add', args=(camera.id,)))
            else:
                return redirect(reverse(
                    'camera-back-detail', args=(camera.id, camera_back.id)
                ))
        else:
            # TODO: Output the actual error from the form instead of this
            # hardcoded one.
            messages.error(request, 'You already have that back.')
            return redirect(reverse('camera-back-add', args=(camera.id)),)
    else:
        form = CameraBackForm()
        context = {
            'owner': owner,
            'form': form,
            'camera': camera,
        }

        return render(request, 'inventory/camera_back_add.html', context)


@login_required
def camera_edit(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)

    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)

        if form.is_valid():
            name = form.cleaned_data['name']
            format = form.cleaned_data['format']
            notes = form.cleaned_data['notes']
            unavailable = form.cleaned_data['unavailable']
            if unavailable and camera.status != 'loaded':
                camera.status = 'unavailable'
            elif camera.status != 'loaded':
                camera.status = 'empty'
            camera.name = name
            camera.format = format
            camera.notes = notes
            camera.save()

            messages.success(request, 'Camera updated!')
            return redirect(reverse('camera-detail', args=(camera.id,)))
    else:
        form = CameraForm(instance=camera)
        form.fields['unavailable'].initial = camera.status == 'unavailable'

        context = {
            'owner': owner,
            'form': form,
            'camera': camera,
            'js_needed': True,
        }

        return render(request, 'inventory/camera_edit.html', context)


@login_required
def camera_back_edit(request, pk, back_pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)
    camera_back = get_object_or_404(CameraBack, id=back_pk, camera=camera)

    if request.method == 'POST':
        form = CameraBackForm(request.POST, instance=camera_back)

        if form.is_valid():
            name = form.cleaned_data['name']
            notes = form.cleaned_data['notes']
            unavailable = form.cleaned_data['unavailable']
            if unavailable and camera_back.status != 'loaded':
                camera_back.status = 'unavailable'
            elif camera_back.status != 'loaded':
                camera_back.status = 'empty'
            camera_back.name = name
            camera_back.notes = notes
            camera_back.save()

            messages.success(request, 'Camera back updated!')
            return redirect(
                reverse('camera-back-detail', args=(camera.id, camera_back.id))
            )
    else:
        form = CameraBackForm(instance=camera_back)
        camera_back_status = camera_back.status == 'unavailable'
        form.fields['unavailable'].initial = camera_back_status

        context = {
            'owner': owner,
            'form': form,
            'camera': camera,
            'camera_back': camera_back,
            'js_needed': True,
        }

        return render(request, 'inventory/camera_back_edit.html', context)


@require_POST
@login_required
def camera_delete(request, pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)
    name = camera.name

    camera.delete()

    messages.success(
        request,
        f'Camera “{name}” successfully deleted.'
    )
    return redirect(reverse('index'))


@require_POST
@login_required
def camera_back_delete(request, pk, back_pk):
    owner = request.user
    camera = get_object_or_404(Camera, id=pk, owner=owner)
    camera_back = get_object_or_404(CameraBack, id=back_pk, camera=camera)
    name = camera_back

    camera_back.delete()

    messages.success(
        request,
        '%s successfully deleted.' % (name)
    )
    return redirect(reverse('camera-detail', args=(camera.id,)))


# EXPORT / IMPORT
# ------
@method_decorator(login_required, name='dispatch')
class ExportRollsView(WriteCSVMixin, View):
    def get(self, request, *args, **kwargs):
        export = self.write_csv('rolls.csv')
        rolls = Roll.objects.filter(owner=request.user)

        export['writer'].writerow([
            'id',
            'code',
            'status',
            'film',
            'film_id',
            'push_pull',
            'camera',
            'camera_id',
            'camera_back',
            'camera_back_id',
            'lens',
            'project',
            'project_id',
            'location',
            'notes',
            'lab',
            'scanner',
            'notes_on_development',
            'created',
            'updated',
            'started',
            'ended',
        ])

        for roll in rolls:
            try:
                camera_id = roll.camera.id
            except AttributeError:
                camera_id = ''
            try:
                camera_back_id = roll.camera_back.id
            except AttributeError:
                camera_back_id = ''
            try:
                project_id = roll.project.id
            except AttributeError:
                project_id = ''

            export['writer'].writerow([
                roll.id,
                roll.code,
                roll.status,
                roll.film,
                roll.film.id,
                roll.push_pull,
                roll.camera,
                camera_id,
                roll.camera_back,
                camera_back_id,
                roll.lens,
                roll.project,
                project_id,
                roll.location,
                roll.notes,
                roll.lab,
                roll.scanner,
                roll.notes_on_development,
                roll.created_at,
                roll.updated_at,
                roll.started_on,
                roll.ended_on,
            ])

        return export['response']


@method_decorator(login_required, name='dispatch')
class ImportRollsView(ReadCSVMixin, RedirectAfterImportMixin, View):
    def post(self, request, *args, **kwargs):
        reader = self.read_csv(request)

        if not reader:
            return redirect(reverse('settings'))

        count = 0

        for row in reader:
            obj, created = Roll.objects.get_or_create(
                owner=request.user,
                id=row['id'],
                film=get_object_or_404(Film, id=row['film_id']),
            )

            if created:
                count += 1

                # Add optional foreign keys
                if row['camera_id']:
                    obj.camera = get_object_or_404(Camera, id=row['camera_id'], owner=request.user)
                if row['camera_back_id']:
                    obj.camera_back = get_object_or_404(
                        CameraBack,
                        id=row['camera_back_id'],
                        camera__owner=request.user
                    )
                if row['project_id']:
                    obj.project = get_object_or_404(Project, id=row['project_id'], owner=request.user)

                # Add optional dates
                if row['started']:
                    obj.started_on = datetime.datetime.strptime(row['started'], '%Y-%m-%d').date()
                if row['ended']:
                    obj.ended_on = datetime.datetime.strptime(row['ended'], '%Y-%m-%d').date()

                # Set status after potentially setting the camera, started, and
                # ended so things are happy with the Roll model’s automatic `save`
                # fanciness.
                obj.status = row['status']

                obj.save()

                Roll.objects.filter(id=row['id'], owner=request.user).update(
                    code=row['code'],
                    push_pull=row['push_pull'],
                    location=row['location'],
                    lens=row['lens'],
                    notes=row['notes'],
                    lab=row['lab'],
                    scanner=row['scanner'],
                    notes_on_development=row['notes_on_development'],
                    # Keep the original created and updated dates and times.
                    created_at=row['created'],
                    updated_at=row['updated'],
                )

        item = {
            'noun': 'roll',
        }

        return self.redirect(request, count, item)


@method_decorator(login_required, name='dispatch')
class ExportCamerasView(WriteCSVMixin, View):
    def get(self, request, *args, **kwargs):
        export = self.write_csv('cameras.csv')
        cameras = Camera.objects.filter(owner=request.user)

        export['writer'].writerow([
            'id',
            'format',
            'name',
            'notes',
            'status',
            'multiple_backs',
            'created',
            'updated',
        ])

        for camera in cameras:
            export['writer'].writerow([
                camera.id,
                camera.format,
                camera.name,
                camera.notes,
                camera.status,
                camera.multiple_backs,
                camera.created_at,
                camera.updated_at,
            ])

        return export['response']


@method_decorator(login_required, name='dispatch')
class ImportCamerasView(ReadCSVMixin, RedirectAfterImportMixin, View):
    def post(self, request, *args, **kwargs):
        reader = self.read_csv(request)

        if not reader:
            return redirect(reverse('settings'))

        count = 0

        for row in reader:
            obj, created = Camera.objects.get_or_create(
                owner=request.user,
                id=row['id'],
                format=row['format'],
                name=row['name'],
            )

            if created:
                count += 1

                Camera.objects.filter(id=row['id'], owner=request.user).update(
                    notes=row['notes'],
                    status=row['status'],
                    multiple_backs=row['multiple_backs'],
                    # Keep the original created and updated dates and times.
                    created_at=row['created'],
                    updated_at=row['updated'],
                )

        item = {
            'noun': 'camera',
        }

        return self.redirect(request, count, item)


@method_decorator(login_required, name='dispatch')
class ExportCameraBacksView(WriteCSVMixin, View):
    def get(self, request, *args, **kwargs):
        export = self.write_csv('camera-backs.csv')
        camera_backs = CameraBack.objects.filter(camera__owner=request.user)

        export['writer'].writerow([
            'id',
            'camera',
            'camera_id',
            'name',
            'notes',
            'status',
            'format',
            'created',
            'updated',
        ])

        for back in camera_backs:
            export['writer'].writerow([
                back.id,
                back.camera,
                back.camera.id,
                back.name,
                back.notes,
                back.status,
                back.format,
                back.created_at,
                back.updated_at,
            ])

        return export['response']


@method_decorator(login_required, name='dispatch')
class ImportCameraBacksView(ReadCSVMixin, RedirectAfterImportMixin, View):
    def post(self, request, *args, **kwargs):
        reader = self.read_csv(request)

        if not reader:
            return redirect(reverse('settings'))

        count = 0

        for row in reader:
            obj, created = CameraBack.objects.get_or_create(
                id=row['id'],
                camera=get_object_or_404(Camera, id=row['camera_id'], owner=request.user),
                name=row['name'],
                format=row['format'],
            )

            if created:
                count += 1

                CameraBack.objects.filter(id=row['id'], camera__owner=request.user).update(
                    notes=row['notes'],
                    status=row['status'],
                    # Keep the original created and updated dates and times.
                    created_at=row['created'],
                    updated_at=row['updated'],
                )

        item = {
            'noun': 'camera back',
        }

        return self.redirect(request, count, item)


@method_decorator(login_required, name='dispatch')
class ExportProjectsView(WriteCSVMixin, View):
    def get(self, request, *args, **kwargs):
        export = self.write_csv('projects.csv')
        projects = Project.objects.filter(owner=request.user)

        export['writer'].writerow([
            'id',
            'name',
            'notes',
            'status',
            'camera_ids',
            'cameras',
            'roll_ids',
            'rolls',
            'created',
            'updated',
        ])

        for project in projects:
            roll_objects = Roll.objects.filter(project=project, owner=request.user)
            roll_ids = []
            rolls = []
            for roll in roll_objects:
                roll_ids.append(roll.id)
                roll_code = f'{roll.code} / ' if roll.code else ''
                roll_name = f'{roll_code}{roll.film.__str__()} / {roll.get_status_display()}'
                rolls.append(roll_name)
            camera_objects = Camera.objects.filter(project=project)
            camera_ids = []
            cameras = []
            for camera in camera_objects:
                camera_ids.append(camera.id)
                cameras.append(camera.__str__())

            export['writer'].writerow([
                project.id,
                project.name,
                project.notes,
                project.status,
                camera_ids,
                cameras,
                roll_ids,
                rolls,
                project.created_at,
                project.updated_at,
            ])

        return export['response']


@method_decorator(login_required, name='dispatch')
class ImportProjectsView(ReadCSVMixin, RedirectAfterImportMixin, View):
    def post(self, request, *args, **kwargs):
        reader = self.read_csv(request)

        if not reader:
            return redirect(reverse('settings'))

        count = 0

        for row in reader:
            roll_ids = json.loads(row['roll_ids'])
            camera_ids = json.loads(row['camera_ids'])

            obj, created = Project.objects.get_or_create(
                owner=request.user,
                id=row['id'],
                name=row['name'],
            )

            if created:
                count += 1

                if roll_ids:
                    for id in roll_ids:
                        roll = get_object_or_404(Roll, id=id, owner=request.user)
                        roll.project = obj
                        roll.save()

                if camera_ids:
                    for id in camera_ids:
                        obj.cameras.add(get_object_or_404(Camera, id=id, owner=request.user))

                    obj.save()

                Project.objects.filter(id=row['id'], owner=request.user).update(
                    notes=row['notes'],
                    status=row['status'],
                    # Keep the original created and updated dates and times.
                    created_at=row['created'],
                    updated_at=row['updated'],
                )

        item = {
            'noun': 'project',
        }

        return self.redirect(request, count, item)


@method_decorator(login_required, name='dispatch')
class ExportJournalsView(WriteCSVMixin, View):
    def get(self, request, *args, **kwargs):
        export = self.write_csv('journals.csv')
        journals = Journal.objects.filter(roll__owner=request.user)

        export['writer'].writerow([
            'id',
            'roll_id',
            'roll',
            'date',
            'notes',
            'frame',
            'created',
            'updated',
        ])

        for journal in journals:
            export['writer'].writerow([
                journal.id,
                journal.roll.id,
                journal.roll,
                journal.date,
                journal.notes,
                journal.frame,
                journal.created_at,
                journal.updated_at,
            ])

        return export['response']


@method_decorator(login_required, name='dispatch')
class ImportJournalsView(ReadCSVMixin, RedirectAfterImportMixin, View):
    def post(self, request, *args, **kwargs):
        reader = self.read_csv(request)

        if not reader:
            return redirect(reverse('settings'))

        count = 0

        for row in reader:
            obj, created = Journal.objects.get_or_create(
                id=row['id'],
                roll=get_object_or_404(Roll, id=row['roll_id'], owner=request.user),
                frame=row['frame'],
            )

            if created:
                count += 1

                Journal.objects.filter(id=row['id'], roll__owner=request.user).update(
                    date=datetime.datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    notes=row['notes'],
                    # Keep the original created and updated dates and times.
                    created_at=row['created'],
                    updated_at=row['updated'],
                )

        item = {
            'noun': 'journal',
        }

        return self.redirect(request, count, item)
