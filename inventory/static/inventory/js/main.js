const confirmDelete = function(item='item') {
    return confirm(`Are you sure you want to delete this ${item}?`);
}

const confirmRemove = function(item='item') {
    return confirm(`Are you sure you want to remove this ${item}?`);
}

const pickmeupOptions = {
    format: 'Y-m-d',
    default_date: false,
    hide_on_select: true,
}

pickmeup('#id_started_on', pickmeupOptions);
pickmeup('#id_ended_on', pickmeupOptions);
