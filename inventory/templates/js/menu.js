/* eslint-disable no-unused-vars */
const menu = document.querySelector('#menu');
const menuInner = document.querySelector('#menu-inner');
const menuOverlay = document.querySelector('#menu-overlay');
const menuContent = document.querySelector('#menu-content');
const openMenuButton = document.querySelector('#menu-open');
const closeMenuButtonWrapper = document.querySelector('#menu-close');
const closeMenuButton = closeMenuButtonWrapper.querySelector('button');
const desktopToggleButton = document.querySelector('#menu-desktop-toggle');

const setupMenu = () => {
  menu.classList.add('-translate-x-full', 'fixed');
  menuInner.classList.add('min-h-screen');
  menuOverlay.classList.add('opacity-0', 'fixed', 'inset-0', 'bg-opacity-75');
  menuContent.classList.add('-translate-x-full', 'max-w-xs');
  openMenuButton.classList.remove('hidden');
  openMenuButton.classList.add('inline-flex');
  closeMenuButtonWrapper.classList.remove('hidden');
  desktopToggleButton.classList.add('md:flex');
};
const openMenu = () => {
  document.body.classList.add('overflow-hidden');
  menu.classList.remove('-translate-x-full');
  menuOverlay.classList.remove('opacity-0');
  menuOverlay.setAttribute('aria-hidden', 'false');
  menu.setAttribute('aria-hidden', 'false');
  menuContent.classList.remove('-translate-x-full');
  setTimeout(() => {
    closeMenuButton.classList.remove('hidden');
  }, 100);
};
const closeMenu = () => {
  document.body.classList.remove('overflow-hidden');
  menuOverlay.classList.add('opacity-0');
  menuOverlay.setAttribute('aria-hidden', 'true');
  menu.setAttribute('aria-hidden', 'true');
  menuContent.classList.add('-translate-x-full');
  setTimeout(() => {
    closeMenuButton.classList.add('hidden');
  }, 100);
  setTimeout(() => {
    menu.classList.add('-translate-x-full');
  }, 300);
};
const desktopToggle = () => {
  menuInner.classList.toggle('collapsed');
  // Set a cookie / localStorage to remember preference.
};

setupMenu();
