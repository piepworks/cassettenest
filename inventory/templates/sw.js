// Bump this version number each time a cached or asset changes.
// If you don't, the SW won't be reinstalled and the pages you cache initially won't be updated
// (by default at least, see next sections for more on caching).
const VERSION = '1';

self.addEventListener('install', () => {
  console.log('[SW] Installing SW version:', VERSION);
});
