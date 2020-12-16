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
