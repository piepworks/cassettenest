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


def status_number(status):
    "Return the status number/order from its name."

    return {
        'storage': '01_storage',
        'loaded': '02_loaded',
        'shot': '03_shot',
        'processing': '04_processing',
        'processed': '05_processed',
        'scanned': '06_scanned',
        'archived': '07_archived',
    }[status]


def pluralize(noun, count):
    if count != 1:
        return noun + 's'
    return noun
