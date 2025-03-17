/* global htmxFade */
window.htmxFade = (opacity) => {
  const elements = document.getElementsByClassName('htmx-replace');
  for (let i = 0; i < elements.length; i++) {
    elements[i].style.opacity = opacity;
  }
};

htmxFade(1.0);

document.body.addEventListener('htmx:beforeRequest', () => {
  htmxFade(0.25);
});

document.body.addEventListener('htmx:afterRequest', () => {
  htmxFade(1.0);
});
