/* global htmx */
window.cnMenu = {
  base: document.querySelector('#menu'),
  inner: document.querySelector('#menu-inner'),
  overlay: document.querySelector('#menu-overlay'),
  content: document.querySelector('#menu-content'),
  openButton: document.querySelector('#menu-open'),
  closeButtonWrapper: document.querySelector('#menu-close'),
  get closeButton() {
    return this.closeButtonWrapper.querySelector('button');
  },
  toggleButton: document.querySelector('#menu-desktop-toggle'),

  setup: function () {
    this.base.classList.add('-translate-x-full', 'fixed');
    this.inner.classList.add('min-h-screen');
    this.overlay.classList.add(
      'opacity-0',
      'fixed',
      'inset-0',
      'bg-opacity-75',
    );
    this.content.classList.add('-translate-x-full', 'max-w-xs');
    this.openButton.classList.remove('hidden');
    this.openButton.classList.add('inline-flex');
    this.closeButtonWrapper.classList.remove('hidden');
    this.toggleButton.classList.add('md:tall:flex');

    // This attempts to keep the desktop menu toggle consistent even when
    // switching and then using htmx's pushstate to go back and forward without
    // a full page reload. Hopefully most people won't see this, because there's
    // a bit of a blip when it happens.
    document.removeEventListener(
      'htmx:historyRestore',
      window.desktopToggleSetup,
    );
    window.desktopToggleSetup = () => {
      fetch('{% url "session-sidebar-status" %}', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then((response) => response.text())
        .then((text) => {
          if (text === 'closed') {
            window.cnMenu.inner.classList.add('collapsed');
          } else {
            window.cnMenu.inner.classList.remove('collapsed');
          }
        });
    };
    document.addEventListener('htmx:historyRestore', window.desktopToggleSetup);
  },

  open: function () {
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

  close: function () {
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

  desktopToggle: function () {
    this.inner.classList.toggle('collapsed');
    htmx.ajax('GET', '{% url "session-sidebar" %}', { swap: 'none' });
  },
};

document.body.removeEventListener('keyup', window.cnKeyupBackslash);
window.cnKeyupBackslash = (e) => {
  if (e.code === 'Backslash') {
    window.cnMenu.desktopToggle();
  }
};
document.body.addEventListener('keyup', window.cnKeyupBackslash);

document.body.removeEventListener('keyup', window.cnKeyupEsc);
window.cnKeyupEsc = (e) => {
  if (e.code === 'Escape') {
    window.cnMenu.close();
  }
};
document.body.addEventListener('keyup', window.cnKeyupEsc);

// Close the menu on browser back or forward
window.onpageshow = (e) => {
  if (e.persisted) {
    window.cnMenu.close();
  }
};

window.cnMenu.setup();
