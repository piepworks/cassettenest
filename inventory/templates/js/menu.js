const menu = document.querySelector('#menu');
const menuInner = document.querySelector('#menu-inner');
const menuOverlay = document.querySelector('#menu-overlay');
const menuContent = document.querySelector('#menu-content');
const openMenuButton = document.querySelector('#menu-open');
const closeMenuButtonWrapper = document.querySelector('#menu-close');

const setupMenu = () => {
  menu.classList.add('-translate-x-full', 'fixed');
  menuInner.classList.add('min-h-screen');
  menuOverlay.classList.add('opacity-0', 'fixed', 'inset-0', 'bg-opacity-75');
  menuContent.classList.add('-translate-x-full', 'max-w-xs');
  openMenuButton.classList.remove('hidden');
  openMenuButton.classList.add('inline-flex');
  closeMenuButtonWrapper.classList.remove('hidden');
};

setupMenu();
