import datetime
import json
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, DetailView, FormView
from django.db.models import Count, Q
from django.db import IntegrityError, transaction
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_str
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings as dj_settings
from itertools import chain
import requests
from .models import Camera, CameraBack, Stock, Film, Manufacturer, Journal, Project, Roll, Frame
from .forms import (
    CameraForm,
    CameraBackForm,
    JournalForm,
    PatternsForm,
    ProfileForm,
    ProjectForm,
    ReadyForm,
    RegisterForm,
    RollForm,
    StepperForm,
    StockForm,
    UserForm,
    UploadCSVForm,
    FrameForm,
)
from .utils import (
    development_statuses,
    bulk_status_keys,
    get_project_or_none,
    pluralize,
    status_description,
    status_keys,
    status_number,
    bulk_status_next_keys,
    send_email_to_trey,
    inventory_filter,
    preset_apertures,
    preset_shutter_speeds,
    available_types,
    SectionTabs,
    film_types,
)
from .decorators import user_account_active, user_account_inactive
from .utils_paddle import (
    supported_webhooks,
    is_valid_plan,
    is_valid_webhook,
    is_valid_ip_address,
    paddle_plan_name,
    update_subscription,
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
    cameras_unavailable = cameras_total.filter(status='unavailable')
    rolls = Roll.objects.filter(owner=owner)
    rolls_loaded = rolls.filter(status=status_number('loaded'))
    all_projects = Project.objects.filter(
        owner=owner,
    ).order_by('-updated_at',)

    cameras = SectionTabs(
        'Cameras',
        '#homepage_sections',
        0,
        [
            {
                'name': 'Loaded',
                'count': rolls_loaded.count(),
                'rows': rolls_loaded,
                'action': 'roll'
            },
            {
                'name': 'Ready to Load',
                'count': cameras_empty.count() + camera_backs_empty.count(),
                'rows': list(chain(cameras_empty, camera_backs_empty)),
                'action': 'load',
            },
            {
                'name': 'Unavailable',
                'count': cameras_unavailable.count(),
                'rows': cameras_unavailable,
                'action': 'load',
            },
        ],
        reverse('camera-add'),
    )

    projects = SectionTabs(
        'Projects',
        '#homepage_sections',
        0,
        [
            {
                'name': 'Current',
                'count': all_projects.filter(status='current').count(),
                'rows': all_projects.filter(status='current'),
            },
            {
                'name': 'Archived',
                'count': all_projects.filter(status='archived').count(),
                'rows': all_projects.filter(status='archived'),
            }
        ],
        reverse('project-add'),
    )

    if request.GET.get('c'):
        cameras.set_tab(request.GET.get('c'))

    if request.GET.get('p'):
        projects.set_tab(request.GET.get('p'))

    if request.htmx:
        slug = request.GET.get('slug')
        c = request.GET.get('c') if request.GET.get('c') else 0
        p = request.GET.get('p') if request.GET.get('p') else 0

        if slug == 'c':
            cameras.set_tab(c)
        elif slug == 'p':
            projects.set_tab(p)

        context = {
            'cameras': cameras,
            'projects': projects,
        }

        response = render(request, 'partials/homepage-sections.html', context)
        response['HX-Push'] = reverse('index') + f'?c={c}&p={p}'

        return response

    else:
        context = {
            'email': owner.email,
            'cameras': cameras,
            'cameras_total': cameras_total,
            'projects': projects,
            'rolls': rolls,
            'film_types': film_types,
        }

        return render(request, 'inventory/index.html', context)


def patterns(request):
    from django.contrib.messages.storage.base import Message

    test_messages = [
        Message(0, 'Yay!', 'success'),
        Message(0, 'Whoops!', 'error'),
        Message(0, 'Uh oh!', 'warning'),
        Message(0, 'Ah!', 'info'),
    ]

    test_rolls = {
        'all': 123,
        '135': 4,
        '120': 119,
        'c41': {
            'all': 1,
            '135': 5,
            '120': 1,
            'push2': {
                '135': 77,
                '120': 1,
            }
        },
        'bw': {
            'all': 500,
            '135': 4,
            '120': 75,
            'push3': {
                '135': 88,
                '120': 8,
            }
        },
        'e6': {
            'all': 100,
            '135': 1,
            '120': 7000,
            'pull1': {
                '135': 84,
                '120': 45,
            }
        },
    }

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

    paddle = {
        'live_mode': dj_settings.PADDLE_LIVE_MODE,
        'vendor_id': dj_settings.PADDLE_VENDOR_ID,
        'standard_monthly_id': int(dj_settings.PADDLE_STANDARD_MONTHLY),
        'standard_annual_id': int(dj_settings.PADDLE_STANDARD_ANNUAL),
        'awesome_annual_id': int(dj_settings.PADDLE_AWESOME_ANNUAL),
        'standard_monthly_name': paddle_plan_name(dj_settings.PADDLE_STANDARD_MONTHLY),
        'standard_annual_name': paddle_plan_name(dj_settings.PADDLE_STANDARD_ANNUAL),
        'awesome_annual_name': paddle_plan_name(dj_settings.PADDLE_AWESOME_ANNUAL),
    }

    subscription_never = {
        'active': False,
        'trial': {'enabled': True, 'duration': 14},
    }

    subscription_monthly = {
        'active': True,
        'plan': paddle['standard_monthly_name'],
        'plan_id': paddle['standard_monthly_id'],
        'update_url': 'https://example.com',
        'cancel_url': 'https://example.com',
    }

    subscription_annual = {
        'active': True,
        'plan': paddle['standard_annual_name'],
        'plan_id': paddle['standard_annual_id'],
        'update_url': 'https://example.com',
        'cancel_url': 'https://example.com',
    }

    subscription_friend = {
        'friend': True,
    }

    subscription_scheduled = {
        'active': True,
        'status': 'deleted',
        'plan': paddle['standard_monthly_name'],
        'plan_id': paddle['standard_monthly_id'],
        'cancellation_date': datetime.date.today() + datetime.timedelta(days=1),
    }

    subscription_trial = {
        'active': True,
        'status': 'trialing',
        'plan': paddle['standard_monthly_name'],
        'plan_id': paddle['standard_monthly_id'],
        'trial_days_remaining': 2,
        'update_url': 'https://example.com',
        'cancel_url': 'https://example.com',
    }

    context = {
        'test_rolls': test_rolls,
        'test_messages': test_messages,
        'form': PatternsForm,
        'roll1': roll1,
        'roll2': roll2,
        'roll3': roll3,
        'js_needed': True,
        'wc_needed': True,
        'paddle': paddle,
        'subscription_never': subscription_never,
        'subscription_monthly': subscription_monthly,
        'subscription_annual': subscription_annual,
        'subscription_friend': subscription_friend,
        'subscription_scheduled': subscription_scheduled,
        'subscription_trial': subscription_trial,
    }

    return render(request, 'patterns.html', context)


def marketing_site(request):
    if request.user.is_authenticated:
        return HttpResponse('You are logged in.')
    else:
        return HttpResponseForbidden('You are not logged in.')


@user_account_inactive
@login_required
def account_inactive(request):
    context = {}
    return render(request, 'account-inactive.html', context)


@login_required
def settings(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user)

        if user_form.is_valid() and profile_form.is_valid():
            user = request.user
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
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
        csv_form = UploadCSVForm()
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
        trial = {
            'enabled': dj_settings.SUBSCRIPTION_TRIAL,
            'duration': dj_settings.SUBSCRIPTION_TRIAL_DURATION,
        }

        plan_name = ''
        if request.user.profile.paddle_subscription_plan_id:
            plan_name = paddle_plan_name(request.user.profile.paddle_subscription_plan_id)

        cancellation_date = None
        if request.user.profile.paddle_cancellation_date:
            cancellation_date = request.user.profile.paddle_cancellation_date

        try:
            trial_days_remaining = request.user.profile.trial_days_remaining
        except AttributeError:
            trial_days_remaining = None

        paddle = {
            'live_mode': dj_settings.PADDLE_LIVE_MODE,
            'vendor_id': dj_settings.PADDLE_VENDOR_ID,
            'standard_monthly_id': int(dj_settings.PADDLE_STANDARD_MONTHLY),
            'standard_annual_id': int(dj_settings.PADDLE_STANDARD_ANNUAL),
            'awesome_annual_id': int(dj_settings.PADDLE_AWESOME_ANNUAL),
            'standard_monthly_name': paddle_plan_name(dj_settings.PADDLE_STANDARD_MONTHLY),
            'standard_annual_name': paddle_plan_name(dj_settings.PADDLE_STANDARD_ANNUAL),
            'awesome_annual_name': paddle_plan_name(dj_settings.PADDLE_AWESOME_ANNUAL),
            'plan_name': plan_name,
        }

        # All the bits about a subscription to be able to show the subscription
        # section on this page.
        subscription = {
            'friend': request.user.is_staff or request.user.profile.friend,
            'status': request.user.profile.subscription_status,
            'active': request.user.profile.has_active_subscription,
            'plan': plan_name,
            'plan_id': request.user.profile.paddle_subscription_plan_id,
            'trial': trial,
            'trial_days_remaining': trial_days_remaining,
            'cancellation_date': cancellation_date,
            'update_url': request.user.profile.paddle_update_url,
            'cancel_url': request.user.profile.paddle_cancel_url,
        }

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'csv_form': csv_form,
            'exportable': exportable,
            'exportable_data': exportable_data,
            'imports': imports,
            'js_needed': True,
            'trial': trial,
            'paddle': paddle,
            'subscription': subscription,
        }

        return render(request, 'inventory/settings.html', context)


@login_required
def subscription_created(request):
    # For Paddle
    subscription_message = ''

    if request.GET.get('plan'):
        try:
            plan = paddle_plan_name(request.GET.get('plan'))
            subscription_message = f' to the {plan} plan'
        except KeyError:
            pass

    messages.success(
        request,
        f'You’re subscribed{subscription_message}! It may take a moment to show up in your settings.'
    )

    return redirect('settings')


@require_POST
@csrf_exempt
def paddle_webhooks(request):
    forwarded_for = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))

    if not is_valid_ip_address(forwarded_for):
        return HttpResponseForbidden('Permission denied.')

    payload = request.POST.dict()

    if not is_valid_webhook(payload):
        return HttpResponse(status=400)

    alert_name = payload.get('alert_name')
    cn_user_id = payload.get('passthrough')

    if not alert_name or not cn_user_id:
        return HttpResponse(status=400)

    if alert_name in supported_webhooks:
        user = get_object_or_404(User, id=cn_user_id)
        update_subscription(alert_name, user, payload)

    return HttpResponse(status=200)


@require_POST
@login_required
def subscription_update(request):
    # https://developer.paddle.com/api-reference/intro/api-authentication
    # https://developer.paddle.com/api-reference/subscription-api/users/updateuser
    plan = request.POST.get('plan')
    sandbox = ''
    if dj_settings.PADDLE_LIVE_MODE == 0:
        sandbox = 'sandbox-'

    if is_valid_plan(plan):
        r = requests.post(
            f'https://{sandbox}vendors.paddle.com/api/2.0/subscription/users/update',
            data={
                'vendor_id': dj_settings.PADDLE_VENDOR_ID,
                'vendor_auth_code': dj_settings.PADDLE_VENDOR_AUTH_CODE,
                'subscription_id': request.user.profile.paddle_subscription_id,
                'plan_id': plan,
            }
        )

        if r.json()['success'] is True:
            messages.success(
                request,
                f'Your plan is now set to {paddle_plan_name(plan)}. It may take a moment to show up in your settings.'
            )
        else:
            error = r.json()['error']['message']
            messages.error(request, f'There was a problem changing plans. “{error}” Please try again.')
    else:
        messages.error(request, f'There was a problem changing plans. Please try again.')

    return redirect('settings')


def stocks(request, manufacturer='all'):
    filters = {
        'manufacturer': manufacturer,
        'type': 'all',
    }
    m = None
    type_name = 'all'
    type_passthrough = ''

    if request.GET.get('type') and request.GET.get('type') != 'all':
        filters['type'] = request.GET.get('type')
        type_passthrough = f'?type={filters["type"]}'

    if request.GET.get('manufacturer') and request.GET.get('manufacturer') != 'all':
        filters['manufacturer'] = request.GET.get('manufacturer')

        # If this request wasn't sent by JS, redirect to the canonical URL.
        if not request.htmx:
            return redirect(reverse('stocks-manufacturer', args=(filters['manufacturer'],)) + type_passthrough)

    if request.user.is_authenticated:
        # Exclude stocks that are flagged as `personal` and not created by the current user.
        manufacturers = Manufacturer.objects.all().exclude(
            Q(personal=True) & ~Q(added_by=request.user)
        )
        stocks = Stock.objects.all().exclude(
            Q(personal=True) & ~Q(added_by=request.user)
        ).annotate(count=Count('film')).order_by(
            'type',
            'manufacturer__name',
            'name',
        )
    else:
        manufacturers = Manufacturer.objects.all().exclude(Q(personal=True))
        stocks = Stock.objects.all().exclude(
            Q(personal=True)
        ).annotate(count=Count('film')).order_by(
            'type',
            'manufacturer__name',
            'name',
        )

    type_names = dict(Stock._meta.get_field('type').flatchoices)
    type_choices = {}

    if filters['manufacturer'] != 'all':
        m = get_object_or_404(Manufacturer, slug=filters['manufacturer'])
        stocks = stocks.filter(manufacturer=m)
        type_choices = available_types(request, Stock, type_names, type_choices, m)
    else:
        type_choices = type_names

    if filters['type'] != 'all':
        stocks = stocks.filter(type=filters['type'])
        try:
            type_name = type_choices[filters['type']]
        except KeyError:
            # If the given type doesn’t exist for the manufacturer, redirect without a type filter.
            return redirect(reverse('stocks-manufacturer', args=(filters['manufacturer'],)))

    context = {
        'manufacturer': m,
        'manufacturers': manufacturers,
        'stocks': stocks,
        'filters': filters,
        'type_choices': type_choices,
        'type_name': type_name,
        'js_needed': True,
    }

    if request.htmx:
        # Tell HTMX to use our proper URLs rather than querystrings…
        if filters['manufacturer'] != 'all':
            clean_url = reverse('stocks-manufacturer', args=(filters['manufacturer'],))
        else:
            clean_url = reverse('stocks')

        response = render(request, 'inventory/_stocks-content.html', context)
        response['HX-Push'] = clean_url + type_passthrough

        return response
    else:
        return render(request, 'inventory/stocks.html', context)


def stock(request, manufacturer, slug):
    manufacturer = get_object_or_404(Manufacturer, slug=manufacturer)
    stock = get_object_or_404(Stock, manufacturer=manufacturer, slug=slug)

    if request.user.is_authenticated:
        if stock.personal and stock.added_by != request.user:
            raise Http404()

        films = Film.objects.filter(stock=stock).exclude(
            Q(personal=True) & ~Q(added_by=request.user)
        ).annotate(count=Count('roll'))
    else:
        if stock.personal:
            raise Http404()

        films = Film.objects.filter(stock=stock).exclude(Q(personal=True)).annotate(count=Count('roll'))

    films_list = []
    total_rolls = 0
    total_inventory = 0
    total_history = 0
    for film in films:
        user_inventory_count = None
        user_history_count = None
        if request.user.is_authenticated:
            user_inventory_count = Roll.objects.filter(
                owner=request.user, film=film, status=status_number('storage')
            ).count()
            user_history_count = Roll.objects.filter(
                owner=request.user, film=film
            ).exclude(
                status=status_number('storage')
            ).count()
            total_inventory = total_inventory + user_inventory_count
            total_history = total_history + user_history_count

        films_list.append({
            'name': film.get_format_display(),
            'url': film.get_absolute_url(),
            'type': film.stock.type,
            'count': film.count,
            'user_inventory_count': user_inventory_count,
            'user_history_count': user_history_count,
        })
        total_rolls = total_rolls + film.count

    headings = ['Format', 'Count']
    total_rolls_table = {
        'headings': headings,
        'rows': [{'columns': [film.get_format_display(), film.count] for film in films}],
    }
    total_inventory_table = {
        'headings': headings,
        'rows': [{'columns': [film['name'], film['user_inventory_count']] for film in films_list}]
    }
    total_history_table = {
        'headings': headings,
        'rows': [{
            'columns': [
                {'title': film['name'], 'href': f'{film["url"]}#film_history_heading'},
                film['user_history_count'],
            ]
        } for film in films_list]
    }

    context = {
        'films': films,
        'total_rolls': total_rolls,
        'total_inventory': total_inventory,
        'total_history': total_history,
        'stock': stock,
        'manufacturer': manufacturer,
        'total_rolls_table': total_rolls_table,
        'total_inventory_table': total_inventory_table,
        'total_history_table': total_history_table,
    }

    return render(request, 'inventory/stock.html', context)


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

            email = form.cleaned_data.get('email')
            send_email_to_trey(
                subject='New Cassette Nest user!',
                message=f'{username} / {email} signed up!',
            )

            return redirect('index')
    else:
        if request.user.is_authenticated:
            return redirect(reverse('index'))

        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def inventory(request):
    filters = {
        'format': 'all',
        'type': 'all',
        'format_name': 'all',
        'type_name': 'all',
    }
    type_names = dict(Stock._meta.get_field('type').flatchoices)
    format_names = dict(Film._meta.get_field('format').flatchoices)

    # All unused rolls
    total_film_count = Film.objects.filter(
        roll__owner=request.user,
        roll__status=status_number('storage'),
    )
    total_rolls = total_film_count.count()

    # Querystring filters.
    if request.GET.get('format') and request.GET.get('format') != 'all':
        filters['format'] = request.GET.get('format')
        filters['format_name'] = format_names[filters['format']]
        total_film_count = total_film_count.filter(format=filters['format'])

    if request.GET.get('type') and request.GET.get('type') != 'all':
        filters['type'] = request.GET.get('type')
        filters['type_name'] = type_names[filters['type']]
        total_film_count = total_film_count.filter(stock__type=filters['type'])

    film_counts = inventory_filter(request, Film, filters['format'], filters['type'])

    format_counts = Film.objects.filter(
        roll__owner=request.user,
        roll__status=status_number('storage')
    ).values('format').distinct().order_by('-format')

    # Get the display name of formats choices.
    format_choices = dict(Film._meta.get_field('format').flatchoices)
    for format in format_counts:
        format['format_display'] = force_str(
            format_choices[format['format']],
            strings_only=True
        )

    type_counts = Film.objects.filter(
        roll__owner=request.user,
        roll__status=status_number('storage')
    ).values('stock__type').distinct().order_by('stock__type')

    # Get the display name of types choices.
    type_choices = dict(Stock._meta.get_field('type').flatchoices)
    for type in type_counts:
        if type['stock__type'] is not None:
            type['type_display'] = force_str(
                type_choices[type['stock__type']],
                strings_only=True
            )

    context = {
        'total_film_count': total_film_count,
        'total_rolls': total_rolls,
        'film_counts': film_counts,
        'format_counts': format_counts,
        'type_counts': type_counts,
        'filters': filters,
        'js_needed': True,
    }

    if request.htmx:
        type = filters['type']
        format = filters['format']
        querystring = ''

        if type != 'all' or format != 'all':
            querystring = f'?type={type}&format={format}'

        response = render(request, 'inventory/_inventory-content.html', context)
        response['HX-Push'] = reverse('inventory') + querystring

        return response
    else:
        return render(request, 'inventory/inventory.html', context)


@login_required
def logbook(request):
    owner = request.user
    status = 0
    description = 'Everything that’s not in inventory.'
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
    all_years.update({'all': all_years_count})
    pagination_querystring = ''
    status_counts = {
        'all': rolls.count(),
        'loaded': rolls.filter(status=status_number('loaded')).count(),
        'shot': rolls.filter(status=status_number('shot')).count(),
        'processing': rolls.filter(status=status_number('processing')).count(),
        'processed': rolls.filter(status=status_number('processed')).count(),
        'scanned': rolls.filter(status=status_number('scanned')).count(),
        'archived': rolls.filter(status=status_number('archived')).count(),
    }

    for y in rolls.dates('started_on', 'year'):
        count = rolls.filter(started_on__year=y.year).count()
        all_years.update({y.year: count})

    if request.GET.get('status') and request.GET.get('status') in status_keys:
        status = request.GET.get('status')
        pagination_querystring += f'&status={status}'
        if status == 'storage':
            return redirect(reverse('inventory'))

        description = status_description(status)
        rolls = rolls.filter(status=status_number(status))
    elif request.GET.get('status') and request.GET.get('status') == 'all':
        # This is for the sake of submitting the mobile filter/form so we don't
        # leave `?status=all` on the URL.
        return redirect(reverse('logbook'))

    if request.GET.get('year'):
        if request.GET.get('year') == 'all':
            return redirect(reverse('logbook'))

        year = request.GET.get('year')
        pagination_querystring += f'&year={year}'
        rolls = rolls.filter(started_on__year=year)

    # Pagination
    paginator = Paginator(rolls, 10)
    page_number = request.GET.get('page') if request.GET.get('page') else 1
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number)
    bulk_status_next = ''

    if status in bulk_status_keys:
        bulk_status_next = bulk_status_next_keys[status]

    context = {
        'owner': owner,
        'rolls': rolls,
        'status': status,
        'page_obj': page_obj,
        'page_range': page_range,
        'description': description,
        'year': year,
        'all_years': all_years,
        'all_years_count': all_years_count,
        'bulk_status_keys': bulk_status_keys,
        'bulk_status_next': bulk_status_next,
        'status_counts': status_counts,
        'pagination_querystring': pagination_querystring[1:],
    }

    if request.htmx:
        response = render(request, 'partials/logbook-page-data.html', context)
        # response['HX-Push'] = reverse('logbook') + full_querystring

        return response
    else:
        return render(request, 'inventory/logbook.html', context)


@login_required
def ready(request):
    form = ReadyForm()
    rolls = Roll.objects.filter(
        owner=request.user,
        status=status_number('shot')
    ).order_by(
        '-ended_on',
        '-started_on',
        '-code'
    )

    ready_rolls = {
        'c41': rolls.filter(film__stock__type='c41'),
        'bw': rolls.filter(film__stock__type='bw'),
        'e6': rolls.filter(film__stock__type='e6'),
        '135': {
            'all': rolls.filter(film__format=135),
            'c41': rolls.filter(film__format=135, film__stock__type='c41'),
            'bw': rolls.filter(film__format=135, film__stock__type='bw'),
            'e6': rolls.filter(film__format=135, film__stock__type='e6'),
        },
        '120': {
            'all': rolls.filter(film__format=120),
            'c41': rolls.filter(film__format=120, film__stock__type='c41'),
            'bw': rolls.filter(film__format=120, film__stock__type='bw'),
            'e6': rolls.filter(film__format=120, film__stock__type='e6'),
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
    paginator = Paginator(rolls, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'owner': request.user,
        'form': form,
        'rolls': ready_counts,
        'page_obj': page_obj,
        'bulk_status_keys': bulk_status_keys,
        'js_needed': True,
        'wc_needed': True,
    }

    if request.htmx:
        return render(request, 'components/logbook-table.html', {
            'status': 'shot',
            'bulk_status_keys': bulk_status_keys,
            'page_obj': page_obj,
            'page': 'ready',
        })
    else:
        return render(request, 'inventory/ready.html', context)


@user_account_active
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

    if current_status in bulk_status_keys and updated_status in bulk_status_keys:
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


@user_account_active
@login_required
def project_add(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user

            try:
                project.save()
            except IntegrityError:
                messages.error(request, 'You’ve already got a project with that name.')
                return redirect(reverse('project-add'))

            messages.success(request, 'Project added!')
            return redirect(reverse('project-detail', args=(project.id,)))
        else:
            messages.error(request, 'Whoops! That didn’t work. Try again.')
            return redirect(reverse('project-add'))
    else:
        form = ProjectForm()
        context = {
            'form': form,
            'action': 'Add',
            'js_needed': True,
            'wc_needed': True,
        }

        return render(request, 'inventory/project_add_edit.html', context)


@user_account_active
@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, id=pk, owner=request.user)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save()

            if project.status == 'archived':
                rolls = Roll.objects.filter(
                    owner=request.user,
                    project=project,
                    status=status_number('storage')
                )
                roll_count = rolls.count()

                if rolls:
                    rolls.update(project=None)

                    plural = pluralize('roll', roll_count)
                    messages.success(
                        request,
                        f'Project archived and {roll_count} {plural} now available for other projects.'
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
            'form': form,
            'project': project,
            'action': 'Edit',
            'js_needed': True,
            'wc_needed': True,
        }

        return render(request, 'inventory/project_add_edit.html', context)


@user_account_active
@require_POST
@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, id=pk, owner=request.user)
    rolls = Roll.objects.filter(owner=request.user, project=project)
    roll_count = rolls.count()
    rolls.update(project=None)
    project.delete()

    plural = pluralize('roll', roll_count)
    if roll_count:
        messages.success(request, f'Project deleted and {roll_count} {plural} now available for other projects.')
    else:
        messages.success(request, 'Project deleted.')
    return redirect(reverse('projects'))


@login_required
def project_detail(request, pk):
    owner = request.user
    project = get_object_or_404(Project, id=pk, owner=owner)
    c = request.GET.get('c') if request.GET.get('c') else 0
    sectiontab_querystring = f'c={c}'
    page = request.GET.get('page') or 1
    pagination_querystring = f'page={page}'

    # Get all of this user's cameras not already associated with this project.
    cameras_to_add = Camera.objects.filter(owner=owner).exclude(
        pk__in=project.cameras.values_list('pk', flat=True)
    ).exclude(
        status='unavailable'
    )
    cameras_empty = project.cameras.filter(status='empty').exclude(multiple_backs=True)

    camera_backs_empty = []
    for camera in project.cameras.all():
        if camera.multiple_backs:
            for back in camera.camera_backs.all():
                if back.status == ('empty'):
                    camera_backs_empty.append(back)

    ready_to_load = []
    for camera in cameras_empty:
        ready_to_load.append(camera)
    for back in camera_backs_empty:
        ready_to_load.append(back)

    loaded = []
    loaded_roll_list = Roll.objects.filter(
        owner=owner,
        project=project,
        status=status_number('loaded'),
    )
    for roll in loaded_roll_list:
        loaded.append(roll)

    loaded_outside_project = []
    for camera in project.cameras.all():
        for roll in camera.roll_set.all():
            if roll.status == status_number('loaded') and roll.project != project:
                loaded_outside_project.append(roll)

    # Unused rolls already in this project
    total_film_count = Film.objects.filter(
        roll__owner=owner,
        roll__project=project,
        roll__status=status_number('storage'),
    )
    film_counts = total_film_count.annotate(
        count=Count('roll')
    ).order_by(
        'stock__type',
        '-format',
        'stock__manufacturer__name',
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
        'stock__type',
        'stock__manufacturer__name',
        'format',
    )

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

    # TODO: write logic to show either `Cameras` or `Cameras and Backs`.
    cameras = SectionTabs(
        'Cameras and Backs',
        '#project-camera-logbook-wrapper',
        0,
        [
            {
                'name': 'Loaded',
                'count': len(loaded),
                'rows': loaded,
                'action': 'roll',
            },
            {
                'name': 'Ready to load',
                'count': len(ready_to_load),
                'rows': ready_to_load,
                'action': 'load'
            },
            {
                'name': 'Loaded outside of project',
                'count': len(loaded_outside_project),
                'rows': loaded_outside_project,
                'action': 'roll',
            }
        ]
    )
    cameras.set_tab(c)

    # Pagination
    paginator = Paginator(roll_logbook, 10)
    page_number = request.GET.get('page') if request.GET.get('page') else 1
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number)

    # Archived project cameras table
    cameras_table = {}
    if project.status == 'archived':
        cameras_table = {
            'headings': ['Camera'],
            'rows': [{
                'columns': [
                    {
                        'title': camera,
                        'href': camera.get_absolute_url(),
                    },
                ]
            } for camera in project.cameras.all()]
        }

    context = {
        'owner': owner,
        'project': project,
        'cameras_to_add': cameras_to_add,
        'cameras': cameras,
        'total_film_count': total_film_count,
        'total_rolls': total_film_count.count(),
        'film_counts': film_counts,
        'film_available_count': film_available_count,
        'format_counts': format_counts,
        'loaded_roll_list': loaded_roll_list,
        'roll_logbook': roll_logbook,
        'page_obj': page_obj,
        'pagination_querystring': pagination_querystring,
        'sectiontab_querystring': sectiontab_querystring,
        'stepper_form': StepperForm,
        'cameras_table': cameras_table,
    }

    if request.htmx:
        response = render(request, 'partials/project-camera-logbook-wrapper.html', {
            'project': project,
            'cameras': cameras,
            'roll_logbook': roll_logbook,
            'items': cameras,
            'page_obj': page_obj,
            'page_range': page_range,
            'pagination_querystring': pagination_querystring,
            'sectiontab_querystring': sectiontab_querystring,
        })

        querystring = f'?{sectiontab_querystring}&{pagination_querystring}'
        response['HX-Push'] = reverse('project-detail', args=(project.id,)) + querystring

        return response
    else:
        return render(request, 'inventory/project_detail.html', context)


@user_account_active
@require_POST
@login_required
def project_rolls_add(request, pk):
    project = get_object_or_404(Project, id=pk, owner=request.user)
    film = get_object_or_404(Film, id=request.POST.get('film', ''))
    quantity = int(request.POST.get('quantity', ''))
    available_quantity = Roll.objects.filter(
        owner=request.user,
        film=film,
        project=None,
        status=status_number('storage'),
    ).count()

    if quantity <= available_quantity:
        rolls_queryset = Roll.objects.filter(
            owner=request.user,
            film=film,
            project=None,
            status=status_number('storage'),
        ).order_by('-created_at')[:quantity]
        Roll.objects.filter(id__in=rolls_queryset).update(project=project)

        plural = pluralize('roll', quantity)
        messages.success(request, f'{quantity} {plural} of {film} added!')
    else:
        messages.error(request, f'You don’t have that many rolls of {film} available.')

    return redirect(reverse('project-detail', args=(project.id,)))


@user_account_active
@require_POST
@login_required
def project_rolls_remove(request, pk):
    project = get_object_or_404(Project, id=pk, owner=request.user)
    film = get_object_or_404(Film, id=request.POST.get('film', ''))
    rolls = Roll.objects.filter(
        owner=request.user,
        film=film,
        project=project,
        status=status_number('storage'),
    )
    roll_count = rolls.count()
    rolls.update(project=None)

    if roll_count:
        plural = pluralize('roll', roll_count)
        messages.success(request, f'Removed {roll_count} {plural} of {film} from this project!')
    else:
        messages.error(request, f'You don’t have any rolls of {film} to remove.')

    return redirect(reverse('project-detail', args=(project.id,)))


@user_account_active
@require_POST
@login_required
def project_camera_update(request, pk):
    '''
    Add or remove a camera from a project.
    '''
    actions = ('add', 'remove',)
    project = get_object_or_404(Project, id=pk, owner=request.user)
    camera = get_object_or_404(
        Camera,
        id=request.POST.get('camera', ''),
        owner=request.user
    )
    action = request.POST.get('action', '')

    if action in actions:
        if action == 'add':
            project.cameras.add(camera)
            messages.success(request, f'{camera} added to this project!')
        if action == 'remove':
            project.cameras.remove(camera)
            messages.success(request, f'{camera} removed from this project!')
    else:
        messages.error(request, 'Something is amiss.')

    return redirect(reverse('project-detail', args=(project.id,)))


@user_account_active
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
                # https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
                roll.pk = None
                roll._state.adding = True
                roll.save()

            roll_plural = pluralize('roll', quantity)
            messages.success(
                request,
                f'Added {quantity} {roll_plural} of {film}!',
            )
        else:
            messages.error(request, 'Enter a quantity of 1 or more.')

        return redirect(reverse('inventory'))

    else:
        # Exclude films that are flagged as `personal` and not created by the current user.
        films = Film.objects.all().exclude(Q(personal=True) & ~Q(added_by=owner)).order_by('stock')
        context = {
            'films': films,
            'stepper_form': StepperForm,
            'js_needed': True,
        }

        return render(request, 'inventory/rolls_add.html', context)


@user_account_active
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

            roll_url = reverse('roll-detail', args=(roll.id,))
            messages.success(
                request,
                f'Added a roll: <a href="{roll_url}">{roll}</a>!',
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
        films = Film.objects.all().exclude(Q(personal=True) & ~Q(added_by=owner)).order_by('stock')
        form = RollForm()
        form.fields['camera'].queryset = Camera.objects.filter(owner=owner)
        form.fields['camera_back'].queryset = CameraBack.objects.filter(camera__owner=owner)
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
def film_rolls(request, stock=None, format=None, slug=None):
    '''All the rolls of a particular film that someone has or has used.'''

    if stock:
        film = get_object_or_404(Film, stock__slug=stock, format=format)

        if film.personal and film.added_by != request.user:
            raise Http404()
    else:
        film = get_object_or_404(Film, slug=slug)

        if film.personal and film.added_by != request.user:
            raise Http404()

        # If this film does have a stock associated with it, redirect to the new URL.
        if film.stock:
            return redirect(reverse('film-rolls', args=(film.stock.slug, film.format,)))

    current_project = None
    rolls = Roll.objects.filter(owner=request.user, film=film)
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
            request.user,
            request.GET.get('project'),
        )
    if current_project is not None and current_project != 0:
        rolls_storage = rolls_storage.filter(project=current_project)
        rolls_history = rolls_history.filter(project=current_project)

    rolls_storage_table = {
        'headings': ['Added on', 'Project'] if not current_project else ['Added on', ''],
        'rows': [{
            'columns': [
                {
                    'title': roll.created_at.strftime('%B %d, %Y'),
                    'href': reverse('roll-detail', args=(roll.id,)),
                },
                {
                    'title': roll.project.name if roll.project else None,
                    'href': f'?project={roll.project.id}' if roll.project else None
                },
            ]
        } if roll.project and not current_project else {
            'columns': [
                {
                    'title': roll.created_at.strftime('%B %d, %Y'),
                    'href': reverse('roll-detail', args=(roll.id,)),
                },
                '',
            ],
        } for roll in rolls_storage]
    }

    rolls_history_table = {
        'headings': ['Year', 'Code', 'Project'] if not current_project else ['Code', ''],
        'rows': [{
            'columns': [
                roll.started_on.strftime('%Y'),
                {
                    'title': roll.code,
                    'href': reverse('roll-detail', args=(roll.id,)),
                },
                {
                    'title': roll.project.name,
                    'href': f'?project={roll.project.id}',
                }
            ],
        } if roll.project and not current_project else {
            'columns': [
                roll.started_on.strftime('%Y'),
                {
                    'title': roll.code,
                    'href': reverse('roll-detail', args=(roll.id,)),
                },
                '',
            ],
        } for roll in rolls_history]
    }

    context = {
        'rolls_storage': rolls_storage,
        'rolls_history': rolls_history,
        'film': film,
        'owner': request.user,
        'current_project': current_project,
        'rolls_storage_table': rolls_storage_table,
        'rolls_history_table': rolls_history_table,
    }

    return render(request, 'inventory/film_rolls.html', context)


@user_account_active
@login_required
def stock_add(request):
    if request.method == 'POST':
        form = StockForm(request.POST, user=request.user)

        if form.is_valid():
            if form.cleaned_data['new_manufacturer']:
                # Create new manufactuter and get a reference to it.
                new_manufacturer = form.cleaned_data['new_manufacturer']
                try:
                    with transaction.atomic():
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
                        'wc_needed': True,
                    }

                    return render(request, 'inventory/stock_add.html', context)
            else:
                manufacturer = form.cleaned_data['manufacturer']

            # 1. Create stock
            # 2. Create film(s)

            stock = Stock.objects.create(
                personal=True,
                added_by=request.user,
                manufacturer=manufacturer,
                name=form.cleaned_data['name'],
                slug=slugify(form.cleaned_data['name']),
                type=form.cleaned_data['type'],
                iso=form.cleaned_data['iso'],
                url=form.cleaned_data['url'],
                description=form.cleaned_data['description'],
            )

            formats = form.cleaned_data['formats']

            for format in formats:
                Film.objects.create(
                    personal=True,
                    added_by=request.user,
                    stock=stock,
                    format=format,
                )

            format_message = ', '.join(str(f) for f in formats)
            format_message = format_message.replace('135', '35mm')

            messages.success(request, f'New film stock “{stock}” (in {format_message}) added!')

            current_site = get_current_site(request)
            if 'new_manufacturer' in locals():
                message_addendum = f'''“{new_manufacturer}” is a new manufacturer.\n
                    https://{current_site}{reverse('admin:inventory_manufacturer_change', args=(manufacturer.id,))}
                '''
            else:
                message_addendum = ''
            send_email_to_trey(
                subject='New film stock added!',
                message=f'''{request.user} added “{stock} (in {format_message}).”\n
                    https://{current_site}{reverse('admin:inventory_stock_change', args=(stock.id,))}\n
                    {message_addendum}
                ''',
            )

            film_id_to_add = Film.objects.filter(stock=stock).first().id

            if form.cleaned_data['destination'] != 'add-storage':
                if 'another' in request.POST:
                    return redirect(reverse('stock-add') + '?destination=add-logbook')
                else:
                    # Go back to add roll to logbook page.
                    return redirect(reverse('roll-add') + f'?film={film_id_to_add}')
            else:
                if 'another' in request.POST:
                    return redirect('stock-add')
                else:
                    # Go back to add rolls to storage page.
                    return redirect(reverse('rolls-add') + f'?film={film_id_to_add}')
    else:
        destination = request.GET.get('destination')
        if destination:
            form = StockForm(user=request.user, initial={'destination': destination})
        else:
            form = StockForm(user=request.user, initial={'destination': 'add-storage'})

    context = {
        'form': form,
        'js_needed': True,
        'wc_needed': True,
    }

    return render(request, 'inventory/stock_add.html', context)


@login_required
def roll_detail(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)
    journal_entries = Journal.objects.filter(roll=roll).order_by('date')
    frames = Frame.objects.filter(roll=roll).order_by('number')

    context = {
        'owner': owner,
        'roll': roll,
        'development_statuses': development_statuses,
        'journal_entries': journal_entries,
        'frames': frames,
        'js_needed': True,
    }

    return render(request, 'inventory/roll_detail.html', context)


@user_account_active
@login_required
def roll_edit(request, pk):
    owner = request.user
    roll = get_object_or_404(Roll, pk=pk, owner=owner)

    if request.method == 'POST':
        form = RollForm(request.POST, instance=roll)
        camera = None
        camera_back = None

        if roll.camera:
            camera = roll.camera
        if roll.camera_back:
            camera_back = roll.camera_back

        if form.is_valid():
            roll = form.save(commit=False)

            if camera and not form.cleaned_data['camera']:
                roll.camera = camera
            if camera_back and not form.cleaned_data['camera_back']:
                roll.camera_back = camera_back

            roll.save()

            messages.success(request, 'Changes saved!')

            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
        form = RollForm(instance=roll)
        form.fields['project'].queryset = Project.objects.filter(owner=owner)
        form.fields['camera'].queryset = Camera.objects.filter(owner=owner)
        form.fields['camera_back'].queryset = CameraBack.objects.filter(camera__owner=owner)
        status_choices = Roll._meta.get_field('status').flatchoices
        del status_choices[1]  # remove loaded
        form.fields['status'].choices = status_choices

        context = {
            'owner': owner,
            'roll': roll,
            'form': form,
            'js_needed': True,
            'wc_needed': True,
        }

        return render(
            request,
            'inventory/roll_edit.html',
            context
        )


@user_account_active
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


@user_account_active
@login_required
def roll_journal_add(request, roll_pk):
    roll = get_object_or_404(Roll, pk=roll_pk, owner=request.user)

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
            'owner': request.user,
            'roll': roll,
            'form': form,
            'action': 'Add',
            'js_needed': True,
            'wc_needed': True,
        }

        return render(
            request,
            'inventory/roll_journal_add_edit.html',
            context
        )


@user_account_active
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
            'entry': entry,
            'starting_frame': entry.starting_frame,
            'action': 'Edit',
            'js_needed': True,
            'wc_needed': True,
        }

        return render(
            request,
            'inventory/roll_journal_add_edit.html',
            context
        )


@user_account_active
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


@user_account_active
@login_required
def roll_frame_add(request, roll_pk):
    roll = get_object_or_404(Roll, pk=roll_pk, owner=request.user)

    if request.method == 'POST':
        form = FrameForm(request.POST)

        if form.is_valid():
            frame = form.save(commit=False)
            frame.roll = roll

            # Custom fields take precedence over dropdown presets.
            if form.cleaned_data['aperture'] != '':
                frame.aperture = form.cleaned_data['aperture']
            elif form.cleaned_data['aperture_preset'] != '':
                frame.aperture = form.cleaned_data['aperture_preset']

            if form.cleaned_data['shutter_speed'] != '':
                frame.shutter_speed = form.cleaned_data['shutter_speed']
            elif form.cleaned_data['shutter_speed_preset'] != '':
                frame.shutter_speed = form.cleaned_data['shutter_speed_preset']

            try:
                with transaction.atomic():
                    frame.save()

                # Potentially save multiple frames at once.
                ending_number = form.cleaned_data['ending_number']
                if ending_number and ending_number > frame.number:
                    starting_number = frame.number
                    additional_frames = ending_number - starting_number

                    for x in range(1, additional_frames + 1):
                        # https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
                        frame.pk = None
                        frame.number = starting_number + x
                        frame._state.adding = True
                        frame.save()

                    messages.success(request, f'{additional_frames + 1} frames saved!')
                else:
                    messages.success(request, 'Frame saved!')

                if 'another' in request.POST:
                    return redirect(reverse('roll-frame-add', args=(frame.roll.id,)) + '?another')
                else:
                    return redirect(reverse('roll-detail', args=(roll.id,)))
            except IntegrityError:
                messages.error(request, f'This roll already has frame #{frame.number}.')
                return redirect(reverse('roll-frame-add', args=(frame.roll.id,)))
    else:
        try:
            previous_frame = Frame.objects.filter(roll=roll).order_by('number').reverse()[0]
            starting_number = previous_frame.number + 1
            previous_date = previous_frame.date
            previous_aperture = previous_frame.aperture
            previous_shutter_speed = previous_frame.shutter_speed
        except IndexError:
            starting_number = 1

        another = True if 'another' in request.GET else False

        form = FrameForm(initial={
            'number': starting_number,
            'ending_number': starting_number,
            'date': previous_date if another else datetime.date.today(),
            'aperture': previous_aperture if another else '',
            'shutter_speed': previous_shutter_speed if another else '',
        })
        form.fields['ending_number'].widget.attrs['min'] = starting_number

        show_input = {
            'aperture': False,
            'shutter_speed': False,
        }

        if another and previous_aperture in preset_apertures:
            form.fields['aperture_preset'].initial = previous_aperture
        elif another:
            show_input['aperture'] = True

        if another and previous_shutter_speed in preset_shutter_speeds:
            form.fields['shutter_speed_preset'].initial = previous_shutter_speed
        elif another:
            show_input['shutter_speed'] = True

        enhanced_label_aperture = {
            'before': 'ƒ/'
        }

        enhanced_label_shutter_speed = {
            'after': 's',
            'after_tooltip': 'second(s)',
        }

        context = {
            'roll': roll,
            'action': 'Add',
            'form': form,
            'show_input': show_input,
            'enhanced_label_aperture': enhanced_label_aperture,
            'enhanced_label_shutter_speed': enhanced_label_shutter_speed,
            'js_needed': True,
            'wc_needed': True,
        }

        return render(
            request,
            'inventory/roll_frame_add_edit.html',
            context
        )


@login_required
def roll_frame_detail(request, roll_pk, number):
    frame = get_object_or_404(Frame, roll__id=roll_pk, roll__owner=request.user, number=number)
    previous_frame = Frame.objects.filter(number=number - 1, roll__id=roll_pk, roll__owner=request.user).first()
    next_frame = Frame.objects.filter(number=number + 1, roll__id=roll_pk, roll__owner=request.user).first()

    context = {
        'frame': frame,
        'previous_frame': previous_frame,
        'next_frame': next_frame,
        'js_needed': True,
    }

    return render(
        request,
        'inventory/roll_frame_detail.html',
        context
    )


@user_account_active
@login_required
def roll_frame_edit(request, roll_pk, number):
    frame = get_object_or_404(Frame, roll__id=roll_pk, roll__owner=request.user, number=number)

    if request.method == 'POST':
        form = FrameForm(request.POST, instance=frame)

        if form.is_valid():
            frame = form.save(commit=False)

            # Custom fields take precedence over dropdown presets.
            if form.cleaned_data['aperture'] and form.cleaned_data['aperture_preset'] == '':
                frame.aperture = form.cleaned_data['aperture']
            elif form.cleaned_data['aperture_preset'] != '':
                frame.aperture = form.cleaned_data['aperture_preset']

            if form.cleaned_data['shutter_speed'] and form.cleaned_data['shutter_speed_preset'] == '':
                frame.shutter_speed = form.cleaned_data['shutter_speed']
            elif form.cleaned_data['shutter_speed_preset'] != '':
                frame.shutter_speed = form.cleaned_data['shutter_speed_preset']

            try:
                with transaction.atomic():
                    frame.save()

                messages.success(request, 'Frame updated!')
                return redirect(reverse('roll-frame-detail', args=(frame.roll.id, frame.number,)))

            except IntegrityError:
                messages.error(request, f'This roll already has frame #{frame.number}.')
                return redirect(reverse('roll-frame-edit', args=(frame.roll.id, number,)))

    else:
        form = FrameForm(instance=frame)
        show_input = {
            'aperture': False,
            'shutter_speed': False,
        }

        if frame.aperture in preset_apertures:
            form.fields['aperture_preset'].initial = frame.aperture
        else:
            show_input['aperture'] = True

        if frame.shutter_speed in preset_shutter_speeds:
            form.fields['shutter_speed_preset'].initial = frame.shutter_speed
        else:
            show_input['shutter_speed'] = True

        enhanced_label_aperture = {
            'before': 'ƒ/'
        }

        enhanced_label_shutter_speed = {
            'after': 's',
            'after_tooltip': 'second(s)',
        }

        context = {
            'form': form,
            'roll': frame.roll,
            'frame': frame,
            'action': 'Edit',
            'show_input': show_input,
            'enhanced_label_aperture': enhanced_label_aperture,
            'enhanced_label_shutter_speed': enhanced_label_shutter_speed,
            'js_needed': True,
            'wc_needed': True,
        }

        return render(
            request,
            'inventory/roll_frame_add_edit.html',
            context
        )


@user_account_active
@require_POST
@login_required
def roll_frame_delete(request, roll_pk, number):
    frame = get_object_or_404(Frame, roll__id=roll_pk, roll__owner=request.user, number=number)
    name = frame.__str__()

    frame.delete()

    messages.success(
        request,
        f'{name} successfully deleted.'
    )
    return redirect(reverse('roll-detail', args=(roll_pk,)))


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


@user_account_active
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
            f'{camera_or_back} loaded with {roll.film} (code: {roll.code})!'
        )

        if current_project:
            return redirect(reverse(
                'project-detail', args=(current_project.id,))
            )
        else:
            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
        projects = Project.objects.filter(owner=owner, status='current')

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
                count=Count('format')
            ).order_by(
                'stock__type',
                'stock__manufacturer',
            )
            if camera_or_back.format:
                film_counts = film_counts.filter(format=camera_or_back.format)
        else:
            film_counts = Film.objects.filter(
                roll__owner=owner,
                roll__status=status_number('storage')
            ).annotate(
                count=Count('format')
            ).order_by(
                'stock__type',
                'stock__manufacturer',
            )
            if camera_or_back.format:
                film_counts = film_counts.filter(format=camera_or_back.format)

        context = {
            'owner': owner,
            'camera': camera,
            'camera_back': camera_back,
            'camera_or_back': camera_or_back,
            'current_project': current_project,
            'projects': projects,
            'film_counts': film_counts,
            'js_needed': True,
        }

        return render(request, 'inventory/camera_or_back_load.html', context)


@login_required
def camera_or_back_detail(request, pk, back_pk=None):
    camera = get_object_or_404(Camera, id=pk, owner=request.user)
    b = request.GET.get('b') if request.GET.get('b') else 0
    pagination_querystring = ''
    page = request.GET.get('page')
    if page:
        pagination_querystring += f'&page={page}'

    if back_pk:
        camera_back = get_object_or_404(
            CameraBack,
            id=back_pk,
            camera__owner=request.user
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
            f'Roll of {roll.film} (code: {roll.code}) finished!'
        )

        if roll.project:
            return redirect(reverse('project-detail', args=(roll.project.id,)))
        else:
            return redirect(reverse('roll-detail', args=(roll.id,)))
    else:
        roll = ''
        if camera_back:
            rolls_history = Roll.objects.filter(
                owner=request.user,
                camera=pk,
                camera_back=camera_back,
            ).exclude(
                status=status_number('loaded')
            ).order_by(
                '-started_on'
            )
        else:
            rolls_history = Roll.objects.filter(
                owner=request.user,
                camera=pk,
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

        # Pagination
        paginator = Paginator(rolls_history, 10)
        page_number = request.GET.get('page') if request.GET.get('page') else 1
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number)

        context = {
            'owner': request.user,
            'camera': camera,
            'camera_back': camera_back,
            'camera_or_back': camera_or_back,
            'roll': roll,
            'rolls_history': rolls_history,
            'page_obj': page_obj,
            'film_types': film_types,
            'pagination_querystring': pagination_querystring,
            'b': b,
        }

        if camera.multiple_backs:
            all_camera_backs = CameraBack.objects.filter(
                camera__owner=request.user,
                camera=camera,
            )
            loaded_rolls = Roll.objects.filter(
                owner=request.user,
                camera=camera,
                status=status_number('loaded'),
            )

            camera_backs = SectionTabs(
                'Backs',
                '#camera_backs_section',
                0,
                [
                    {
                        'name': 'Loaded',
                        'count': all_camera_backs.filter(status='loaded').count(),
                        'rows': loaded_rolls,
                        'action': 'roll',
                    },
                    {
                        'name': 'Ready to Load',
                        'count': all_camera_backs.filter(status='empty').count(),
                        'rows': all_camera_backs.filter(status='empty'),
                        'action': 'load',
                    },
                    {
                        'name': 'Unavailable',
                        'count': all_camera_backs.filter(status='unavailable').count(),
                        'rows': all_camera_backs.filter(status='unavailable'),
                        'action': 'load',
                    },
                ],
                reverse('camera-back-add', args=(camera.id,)),
            )
            camera_backs.set_tab(b)
            context['camera_backs'] = camera_backs

        if request.htmx:
            if request.htmx.trigger.startswith('section'):
                # Camera backs
                response = render(request, 'components/section.html', {
                    'items': camera_backs,
                    'pagination_querystring': pagination_querystring,
                })
                response['HX-Push'] = reverse('camera-detail', args=(camera.id,)) + f'?b={b}{pagination_querystring}'
                return response
            else:
                return render(request, 'components/logbook-table.html', {
                    'page_obj': page_obj,
                    'page_range': page_range,
                    'pagination_querystring': f'&b={b}',
                })

        else:
            if camera_back:
                return render(request, 'inventory/camera_back_detail.html', context)
            else:
                return render(request, 'inventory/camera_detail.html', context)


@user_account_active
@login_required
def camera_add(request):
    if request.method == 'POST':
        form = CameraForm(request.POST)

        if form.is_valid():
            unavailable = form.cleaned_data['unavailable']
            camera = form.save(commit=False)
            camera.status = 'unavailable' if unavailable else 'empty'
            camera.owner = request.user
            camera.save()

            messages.success(request, 'Camera added!')

            if 'another' in request.POST:
                return redirect('camera-add')
            else:
                return redirect(reverse('camera-detail', args=(camera.id,)))
        else:
            # TODO: Output the actual error from the form instead of this
            # hardcoded one.
            messages.error(request, 'Something is amiss. Please try again.')
            return redirect(reverse('camera-add'),)
    else:
        form = CameraForm()
        context = {
            'form': form,
            'js_needed': True,
            'wc_needed': True,
        }

        return render(request, 'inventory/camera_add.html', context)


@user_account_active
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


@user_account_active
@login_required
def camera_edit(request, pk):
    camera = get_object_or_404(Camera, id=pk, owner=request.user)

    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)

        if form.is_valid():
            unavailable = form.cleaned_data['unavailable']
            camera = form.save(commit=False)
            if unavailable and camera.status != 'loaded':
                camera.status = 'unavailable'
            elif camera.status != 'loaded':
                camera.status = 'empty'
            camera.save()

            messages.success(request, 'Camera updated!')
            return redirect(reverse('camera-detail', args=(camera.id,)))
        else:
            messages.error(request, 'Something is amiss. Please try again.')
            return redirect(reverse('camera-detail', args=(camera.id,)))
    else:
        form = CameraForm(instance=camera)
        form.fields['unavailable'].initial = camera.status == 'unavailable'

        context = {
            'form': form,
            'camera': camera,
            'js_needed': True,
            'wc_needed': True,
        }

        return render(request, 'inventory/camera_edit.html', context)


@user_account_active
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
            'wc_needed': True,
        }

        return render(request, 'inventory/camera_back_edit.html', context)


@user_account_active
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


@user_account_active
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


@login_required
def session_sidebar_status(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseForbidden()

    try:
        status = request.session['sidebar']
    except KeyError:
        status = 'open'

    return HttpResponse(status)


@login_required
def session_sidebar(request):
    if not request.htmx:
        return HttpResponseForbidden()

    try:
        status = request.session['sidebar']
    except KeyError:
        status = 'open'

    request.session['sidebar'] = 'open' if status == 'closed' else 'closed'

    return HttpResponse()


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


@method_decorator(user_account_active, name='dispatch')
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


@method_decorator(user_account_active, name='dispatch')
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


@method_decorator(user_account_active, name='dispatch')
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


@method_decorator(user_account_active, name='dispatch')
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


@method_decorator(user_account_active, name='dispatch')
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
