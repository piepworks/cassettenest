import os
import markdown2
from django.conf import settings


def iso_variables(request):
    range = None
    value = None

    if request.GET.get('iso_range') and request.GET.get('iso_value'):
        ranges = (
            'gte',
            'lte',
            'equals',
        )
        if request.GET.get('iso_range') in ranges:
            range = request.GET.get('iso_range')
            try:
                value = int(request.GET.get('iso_value'))
            except ValueError:
                range = None
                value = None

    return {
        'range': range,
        'value': value
    }


def iso_filter(iso, objects):
    if iso['range'] == 'gte':
        objects = objects.filter(iso__gte=iso['value'])
    elif iso['range'] == 'lte':
        objects = objects.filter(iso__lte=iso['value'])
    elif iso['range'] == 'equals':
        objects = objects.filter(iso=iso['value'])

    return objects


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
