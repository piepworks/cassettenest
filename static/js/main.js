/* eslint-disable no-unused-vars */
const confirmDelete = function(item='item') {
    return confirm(`Are you sure you want to delete this ${item}?`);
};

const confirmRemove = function(item='item') {
    return confirm(`Are you sure you want to remove this ${item}?`);
};

$('html').addClass('has-js');

$('.toggle-button').click(function(e) {
    e.preventDefault();
    let $this = $(this);
    let $toggle = $this.closest('.c-field').next('.toggle');

    $this.text($this.text() === 'Show' ? 'Hide' : 'Show');
    $toggle.toggle();
});

$('.select-all').change((e) => {
    const $selectAllToggle = $(e.target);
    const $tbody = $selectAllToggle.closest('table').find('tbody');
    const $checkboxes = $tbody.find('input[type=checkbox]');
    const $updateButton = $('#update-selected');
    let checked = $selectAllToggle.prop('checked');

    $checkboxes.prop('checked', checked);

    if (checked) {
        $updateButton.val(`Update all ${$checkboxes.length} selected`);
    } else {
        $updateButton.val('Update selected');
    }
});

$('tbody input[type=checkbox]').change((e) => {
    const $tbody = $(e.target).closest('tbody');
    const checkboxCount = $tbody.find('input[type=checkbox]:checked').length;

    $('.select-all').prop('checked', false);

    if (checkboxCount) {
        $('#update-selected').val(`Update ${checkboxCount} selected`);
    } else {
        $('#update-selected').val('Update selected');
    }
});
