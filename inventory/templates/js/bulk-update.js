function updateButtonText() {
    // This is especially crude because we’re assuming only one table on the page.
    const $tbody = $('tbody');
    const $updateButton = $('#update-selected');
    const checkboxesTotal = $tbody.find('input[type=checkbox]').length;
    const checkboxCount = $tbody.find('input[type=checkbox]:checked').length;
    const plural = (checkboxCount !== 1) ? 's' : '';

    if (checkboxCount) {
        $updateButton.attr('disabled', false);
        if (checkboxCount === checkboxesTotal) {
            $('.select-all').prop('checked', true);
        }
        $updateButton.val(`Update ${checkboxCount} selected roll${plural}`);
    } else {
        $updateButton.val('Select rolls to update').attr('disabled', true);
    }
}

$('.select-all').change((e) => {
    const $selectAllToggle = $(e.target);
    const $tbody = $selectAllToggle.closest('table').find('tbody');
    const $checkboxes = $tbody.find('input[type=checkbox]');
    let checked = $selectAllToggle.prop('checked');

    $checkboxes.prop('checked', checked);

    updateButtonText();
});

$('tbody input[type=checkbox]').change(() => {
    $('.select-all').prop('checked', false);
    updateButtonText();
});

// Update the button text on page load.
updateButtonText();