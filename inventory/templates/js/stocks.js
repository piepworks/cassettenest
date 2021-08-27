const $wrapper = $('#stocks-list-wrapper');
const $typeSwitcher = $('#id_type');
const $pageName = $('#page-name');
const $manufacturerName = $('#manufacturer-name');

let stocksUrl = `{% url 'stocks' %}`;
let manufacturerUrl = `{% url 'stocks-manufacturer' manufacturer='m-none' %}`;
let ajaxUrl = `{% url 'stocks-ajax' manufacturer='m-none' type='t-none' %}`;

// {% comment %}These variables are set in `_stocks-list.html`.{% endcomment %}
let typeChoices;
let manufacturerName;
let typeName;

function resetTitle() {
    $manufacturerName.html('');
    $pageName.html('Film Stocks');
    document.title = document.title.replace(/^[^/]+/, 'Film Stocks ');

    if (manufacturerName !== 'None') {
        const titlePrefix = `Film Stocks: ${manufacturerName} `;

        $pageName.html(`<a href="{% url 'stocks' %}">Film Stocks</a>`);
        $pageName.find('a').click((e) => resetLink(e));
        $manufacturerName.html(` &gt; ${manufacturerName}`);
        document.title = document.title.replace('Film Stocks ', titlePrefix);

        if (typeName !== 'all') {
            document.title = document.title.replace(titlePrefix, `${titlePrefix} (${typeName}) `);
        }
    } else {
        if (typeName !== 'all') {
            document.title = document.title.replace('Film Stocks', `Film Stocks: ${typeName} `);
        }
    }
}

function resetManufacturerSelection(manufacturer) {
    const $manufacturerField = $('#id_manufacturer');

    // Update selected manufacturer.
    $manufacturerField.find('option').each((index, element) => {
        if ($(element).val() === manufacturer) {
            $manufacturerField.prop('selectedIndex', index);
        }
    });
}

function resetTypes(type) {
    if (Object.keys(typeChoices).length > 1) {
        $typeSwitcher.html('<option value="all">All types</option>');
        $typeSwitcher.removeAttr('disabled');
    } else {
        $typeSwitcher.html('');
        $typeSwitcher.attr('disabled', 'true');
    }
    for (const key in typeChoices) {
        $typeSwitcher.append(`<option value="${key}">${typeChoices[key]}</option>`);
        if (key === type) {
            $typeSwitcher.find(`option[value=${key}]`).prop('selected', true);
        }
    }
}

function resetLink(e) {
    e.preventDefault();
    const newAjaxUrl = ajaxUrl.replace('t-none', 'all').replace('m-none', 'all');

    $wrapper.html('<div class="loader" />');
    fetch(newAjaxUrl).then((response) =>{
        response.text().then((text) => {
            $wrapper.html(text);
            $('#id_manufacturer').val('all');
            $('#id_type').val('all');
            window.history.pushState({}, '', `{% url 'stocks' %}`);
            resetTypes('all');
            resetTitle();
        });
    });
}

function changeFilters(manufacturer, type='all', changed='all') {
    const newType = (changed === 'type') ? type : 'all';
    const newAjaxUrl = ajaxUrl.replace('t-none', newType).replace('m-none', manufacturer);

    $wrapper.html('<div class="loader" />');
    fetch(newAjaxUrl).then((response) => {
        response.text().then((text) => {
            $wrapper.html(text);
            $('.js-reset-filter').click((e) => resetLink(e));

            if (changed === 'manufacturer') {
                // Reset type selection whenever changing manufacturer.
                resetTypes('all');
            } else {
                resetTypes(type);
            }
            resetManufacturerSelection(manufacturer);
            resetTitle();
        });
    });
}

$('#stock_filter select').change((e) => {
    const url = new URL(window.location);
    const newManufacturer = $('#id_manufacturer').val();
    const newType = $('#id_type').val();
    const changed = (e.target.name === 'manufacturer') ? 'manufacturer' : 'type';

    changeFilters(newManufacturer, newType, changed);

    const newUrl = (newManufacturer === 'all')
        ? stocksUrl
        : manufacturerUrl.replace('m-none', newManufacturer);

    url.pathname = newUrl;
    url.searchParams.set('type', (e.target.name === 'type') ? newType : 'all');
    window.history.pushState({}, '', url);
});

$('.js-reset-filter').click((e) => resetLink(e));
$pageName.find('a').click((e) => resetLink(e));

window.onpopstate = () => {
    const url = new URL(window.location);
    const newType = (url.searchParams.get('type')) ? url.searchParams.get('type') : 'all';
    const newManufacturer = (url.pathname.split('/')[2]) ? url.pathname.split('/')[2] : 'all';

    changeFilters(newManufacturer, newType, 'type');
};
