// Fields & Containers
const $existingManufacturer = $('#id_manufacturer');
const $existingManufacturerContainer = $existingManufacturer.closest('.c-field');
const $newManufacturer = $('#id_new_manufacturer');
const $newManufacturerContainer = $newManufacturer.closest('.c-field');

// Toggle Links
const $showExistingLink = $('<a>…or choose existing manufacturer.</a>');
const $showNewLink = $('<a>…or add a new manufacturer.</a>');

// This field’s border-top should only show up when JavaScript isn’t running.
// This label text makes more sense when its on its own in this progressively-enhanced form.
$newManufacturerContainer.css('border-top', 0).find('label').text('New manufacturer');
$newManufacturerContainer.find('.js-link').append($showExistingLink);
$existingManufacturerContainer.find('.js-link').append($showNewLink);

function showExisting() {
    $newManufacturer.val('').attr('required', false);
    $newManufacturerContainer.hide();
    $existingManufacturerContainer.show();
    $existingManufacturer.attr('required', true);
}

function showNew() {
    $existingManufacturer.attr('required', false);
    $existingManufacturerContainer.hide();
    $newManufacturerContainer.show();
    $newManufacturer.attr('required', true);
}

$showExistingLink.click(() => showExisting());
$showNewLink.click(() => showNew());

showExisting();
