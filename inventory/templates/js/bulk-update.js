/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */
document.addEventListener('alpine:init', () => {
    Alpine.store('checkedCount', 0);
    Alpine.store('itemPlural');
});

const pluralize = itemCount => (itemCount !== 1) ? 's' : '';

const bulkUpdate = function (selector) {
    return {
        selectAll: false,
        allItems: document.querySelectorAll(selector),
        toggleAll() {
            [...this.allItems].map(el => el.checked = this.selectAll);
            Alpine.store('checkedCount', this.selectAll ? this.allItems.length : 0);
        },
        checkboxChange() {
            Alpine.store('checkedCount', document.querySelectorAll(`${selector}:checked`).length);
            Alpine.store('itemPlural', pluralize(Alpine.store('checkedCount')));
            this.selectAll = (Alpine.store('checkedCount') === this.allItems.length) ? true : false;
        },
    };
};
