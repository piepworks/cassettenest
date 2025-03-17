window.confirmDelete = (item = 'this item') =>
  confirm(`Are you sure you want to delete this ${item}?`);

window.confirmRemove = (item = 'this item') =>
  confirm(`Are you sure you want to remove ${item}?`);
