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
    'storage': '01_storage',
    'loaded': '02_loaded',
    'shot': '03_shot',
    'processing': '04_processing',
    'processed': '05_processed',
    'scanned': '06_scanned',
    'archived': '07_archived',
}


status_keys = list(valid_statuses)


# Statuses once a roll has begun development.
# Useful for showing a subset of metadata in some places.
development_statuses = {
    value for key, value in valid_statuses.items()
    if key not in ['storage', 'loaded', 'shot']
}


def status_number(status):
    "Return the status number/order from its name."

    return valid_statuses[status]


def pluralize(noun, count):
    if count != 1:
        return noun + 's'
    return noun
