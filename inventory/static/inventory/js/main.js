const confirmDelete = function(item='item') {
    return confirm(`Are you sure you want to delete this ${item}?`);
}

const confirmRemove = function(item='item') {
    return confirm(`Are you sure you want to remove this ${item}?`);
}

const dateWidgetSupported = function() {
    const input = document.createElement('input');
    input.setAttribute('type', 'date');
    const support = input.type !== 'text';
    delete input;
    return support;
}

if (!dateWidgetSupported()) {
    const pickmeupOptions = {
        format: 'm/d/Y',
        default_date: false,
        hide_on_select: true,
    }

    pickmeup('#id_date', pickmeupOptions);
    pickmeup('#id_started_on', pickmeupOptions);
    pickmeup('#id_ended_on', pickmeupOptions);
}
