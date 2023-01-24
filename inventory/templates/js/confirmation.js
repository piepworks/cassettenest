/* eslint-disable no-unused-vars */
const confirmDelete = function (item = 'this item') {
  return confirm(`Are you sure you want to delete this ${item}?`);
};

const confirmRemove = function (item = 'this item') {
  return confirm(`Are you sure you want to remove ${item}?`);
};
