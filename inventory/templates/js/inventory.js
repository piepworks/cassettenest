const $wrapper = $('#unused-rolls-wrapper');
const $pageName = $('#page-name');
const ajaxUrl = `{% url 'inventory-ajax' format='f-none' type='t-none' %}`;
const $format = $('#id_format');
const $type = $('#id_type');
let formatName = '{{ filters.format_name }}';
let typeName = '{{ filters.type_name }}';

function resetLink(e) {
    e.preventDefault();
    window.history.pushState({}, '', `{% url 'inventory' %}`);

    $format.val('all');
    $type.val('all');

    changeFilters();
}

function resetTitle() {
    const titlePrefix = 'Inventory';
    let newSubtitle = '';

    $pageName.html(titlePrefix);
    document.title = document.title.replace(/^[^/]+/, `${titlePrefix} `);

    if (formatName !== 'all') {
        if (typeName !== 'all') {
            newSubtitle = `${formatName}, ${typeName}`;
        } else {
            newSubtitle = formatName;
        }
    } else {
        if (typeName !== 'all') {
            newSubtitle = typeName;
        }
    }

    if (newSubtitle !== '') {
        $pageName.html(`${titlePrefix} <small>(${newSubtitle})</small>`);
        document.title = document.title.replace(`${titlePrefix} `, `${titlePrefix} (${newSubtitle}) `);
    }
}

function changeFilters(type='all', format='all') {
    const newAjaxUrl = ajaxUrl.replace('f-none', format).replace('t-none', type);

    $wrapper.html('<div class="loader" />');
    fetch(newAjaxUrl).then((response) => {
        response.text().then((text) => {
            $wrapper.html(text);
            $('.js-reset-filter').click((e) => resetLink(e));
            resetTitle();
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
