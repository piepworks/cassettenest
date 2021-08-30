const $wrapper = $('#unused-rolls-wrapper');
const ajaxUrl = `{% url 'inventory-ajax' format='f-none' type='t-none' %}`;
const $format = $('#id_format');
const $type = $('#id_type');

function resetLink(e) {
    e.preventDefault();
    window.history.pushState({}, '', `{% url 'inventory' %}`);

    $format.val('all');
    $type.val('all');

    changeFilters();
}

function changeFilters(type='all', format='all') {
    const newAjaxUrl = ajaxUrl.replace('f-none', format).replace('t-none', type);

    $wrapper.html('<div class="loader" />');
    fetch(newAjaxUrl).then((response) => {
        response.text().then((text) => {
            $wrapper.html(text);
            $('.js-reset-filter').click((e) => resetLink(e));
        });
    });
}

$('#film_filter select').change(() => {
    const url = new URL(window.location);
    const newFormat = $format.val();
    const newType = $type.val();

    url.searchParams.set('format', newFormat);
    url.searchParams.set('type', newType);
    window.history.pushState({}, '', url);

    changeFilters(newType, newFormat);
});

$('.js-reset-filter').click((e) => resetLink(e));

window.onpopstate = () => {
    const url = new URL(window.location);
    const newType = (url.searchParams.get('type')) ? url.searchParams.get('type') : 'all';
    const newFormat = (url.searchParams.get('format')) ? url.searchParams.get('format') : 'all';

    $type.val(newType);
    $format.val(newFormat);

    changeFilters(newType, newFormat);
};
