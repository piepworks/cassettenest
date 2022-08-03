/* global htmx */
if (typeof window.cnMenu === 'undefined') {
  window.cnMenu = {
    base: document.querySelector('#menu'),
    inner: document.querySelector('#menu-inner'),
    overlay: document.querySelector('#menu-overlay'),
    content: document.querySelector('#menu-content'),
    openButton: document.querySelector('#menu-open'),
    closeButtonWrapper: document.querySelector('#menu-close'),
    get closeButton() { return this.closeButtonWrapper.querySelector('button'); },
    toggleButton: document.querySelector('#menu-desktop-toggle'),

    setupMenu: function() {
      this.base.classList.add('-translate-x-full', 'fixed');
      this.inner.classList.add('min-h-screen');
      this.overlay.classList.add('opacity-0', 'fixed', 'inset-0', 'bg-opacity-75');
      this.content.classList.add('-translate-x-full', 'max-w-xs');
      this.openButton.classList.remove('hidden');
      this.openButton.classList.add('inline-flex');
      this.closeButtonWrapper.classList.remove('hidden');
      this.toggleButton.classList.add('md:tall:flex');
    },

    openMenu: function() {
      document.body.classList.add('overflow-hidden');
      this.base.classList.remove('-translate-x-full');
      this.overlay.classList.remove('opacity-0');
      this.overlay.setAttribute('aria-hidden', 'false');
      this.base.setAttribute('aria-hidden', 'false');
      this.content.classList.remove('-translate-x-full');
      setTimeout(() => {
        this.closeButton.classList.remove('hidden');
      }, 100);
    },

    closeMenu: function() {
      document.body.classList.remove('overflow-hidden');
      this.overlay.classList.add('opacity-0');
      this.overlay.setAttribute('aria-hidden', 'true');
      this.base.setAttribute('aria-hidden', 'true');
      this.content.classList.add('-translate-x-full');
      setTimeout(() => {
        this.closeButton.classList.add('hidden');
      }, 100);
      setTimeout(() => {
        this.base.classList.add('-translate-x-full');
      }, 300);
    },

    desktopToggle: function() {
      this.inner.classList.toggle('collapsed');
      htmx.ajax('GET', '{% url "session-sidebar" %}', { swap: 'none' });
    },
  };

  window.cnMenu.setupMenu();
}
