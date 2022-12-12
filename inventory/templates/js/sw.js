/* {% load static %} */
/* global importScripts, workbox */
importScripts('/static/js/vendor/workbox-v6.5.4/workbox-sw.js');

workbox.setConfig({
  modulePathPrefix: '/static/js/vendor/workbox-v6.5.4',
});

workbox.routing.registerRoute(
  ({request}) => request.destination === 'image',
  new workbox.strategies.CacheFirst()
);

workbox.routing.setDefaultHandler(
  new workbox.strategies.NetworkFirst()
);

workbox.recipes.offlineFallback({
  pageFallback: '/offline',
});

// ---

const strategy = new workbox.strategies.CacheFirst();

const urls = [
  `{% static 'tailwind.css' %}`,
  `{% url 'index' %}`,
  `{% url 'inventory' %}`,
  `{% url 'ready' %}`,
  `{% url 'logbook' %}`,
];

workbox.recipes.warmStrategyCache({ urls, strategy });
