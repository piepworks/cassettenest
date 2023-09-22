window.confirmDelete = function (item = 'this item') {
  return confirm(`Are you sure you want to delete this ${item}?`);
};

window.confirmRemove = function (item = 'this item') {
  return confirm(`Are you sure you want to remove ${item}?`);
};
