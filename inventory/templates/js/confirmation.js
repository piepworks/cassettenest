/* eslint-disable no-unused-vars */
const confirmDelete = function (item = 'item') {
    return confirm(`Are you sure you want to delete this ${item}?`);
};

const confirmRemove = function (item = 'item') {
    return confirm(`Are you sure you want to remove this ${item}?`);
};
