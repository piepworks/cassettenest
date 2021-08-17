import os
import markdown2
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count


def get_project_or_none(Project, owner, project_id):
    try:
        current_project = Project.objects.get(
            pk=project_id,
            owner=owner,
        )
    except Project.DoesNotExist:
        current_project = None

    return current_project


valid_statuses = {
    'storage': {
        'number': '01_storage',
        'description': '''
            A roll not yet used. Put it in the fridge if it's gonna be
            a while.
        ''',
    },
    'loaded': {
        'number': '02_loaded',
        'description': '''
            In a camera or film back.
        ''',
    },
    'shot': {
        'number': '03_shot',
        'description': '''
            Ready to be developed.
        ''',
    },
    'processing': {
        'number': '04_processing',
        'description': '''
            Sent to the lab, but you haven't heard from them yet.
        ''',
    },
    'processed': {
        'number': '05_processed',
        'description': '''
            Developed, but not yet scanned.
        ''',
    },
    'scanned': {
        'number': '06_scanned',
        'description': '''
            Scanned, but not put away.
        ''',
    },
    'archived': {
        'number': '07_archived',
        'description': '''
            Done and done. Hopefully safely stored in a sleeve in a binder.
        ''',
    },
}

status_keys = list(valid_statuses)

special_keys = {
    'not_development': ['storage', 'loaded', 'shot'],
    'not_bulk': ['storage', 'loaded']
}

# Statuses once a roll has begun development.
# Useful for showing a subset of metadata in some places.
development_statuses = {
    value['number'] for key, value in valid_statuses.items()
    if key not in special_keys['not_development']
}

# Statuses that can be bulk updated.
# Anything else has to be changed one-at-a-time.
bulk_status_keys = [
    key for key in valid_statuses if key not in special_keys['not_bulk']
]

# The default bulk update option when you’re looking at a given status.
bulk_status_next_keys = {
    'shot': 'processing',
    'processing': 'processed',
    'processed': 'scanned',
    'scanned': 'archived',
    'archived': 'scanned',
}


def status_number(status):
    "Return the status number/order from its name."

    return valid_statuses[status]['number']


def status_description(status):
    "Return a helpful description of the status to display on its page."

    return valid_statuses[status]['description']


def pluralize(noun, count):
    if count != 1:
        return noun + 's'
    return noun


def render_markdown(file):
    file_path = os.path.join(
        settings.BASE_DIR,
        'inventory/templates/',
        file
    )
    return markdown2.markdown_path(file_path)


def get_host(request):
    if settings.DEBUG:
        return f'http://{request.get_host()}'
    else:
        return 'https://app.cassettenest.com'


def send_email_to_trey(subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email='trey@cassettenest.com',
        recipient_list=['boss@treylabs.com']
    )


def inventory_filter(request, Film, format, type):
    film_counts = Film.objects.filter(
        roll__owner=request.user,
        roll__status=status_number('storage'),
    )

    if format != 'all':
        film_counts = film_counts.filter(format=format)

    if type != 'all':
        film_counts = film_counts.filter(stock__type=type)

    return film_counts.annotate(
        count=Count('roll')
    ).order_by(
        'stock__type',
        '-format',
        'manufacturer__name',
        'name',
    )


apertures = [
    ('', '---------'),
    ('1.2', '1.2'),
    ('1.4', '1.4'),
    ('1.8', '1.8'),
    ('2',   '2'),
    ('2.8', '2.8'),
    ('4',   '4'),
    ('5.6', '5.6'),
    ('8',   '8'),
    ('11',  '11'),
    ('16',  '16'),
]

shutter_speeds = [
    ('', '---------'),
    ('2',      '2'),
    ('1',      '1'),
    ('1/2',    '1/2'),
    ('1/4',    '1/4'),
    ('1/8',    '1/8'),
    ('1/15',   '1/15'),
    ('1/30',   '1/30'),
    ('1/60',   '1/60'),
    ('1/125',  '1/125'),
    ('1/250',  '1/250'),
    ('1/500',  '1/500'),
    ('1/1000', '1/1000'),
    ('1/2000', '1/2000'),
    ('1/4000', '1/4000'),
]

preset_apertures = {key for key in dict(apertures)}
preset_shutter_speeds = {key for key in dict(shutter_speeds)}

film_types = [
    ('c41', 'C41 Color'),
    ('bw', 'Black and White'),
    ('e6', 'E6 Color Reversal'),
]

film_formats = [
    ('135', '35mm'),
    ('120', '120'),
]
