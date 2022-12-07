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
  new workbox.strategies.NetworkOnly()
);

workbox.recipes.offlineFallback();
