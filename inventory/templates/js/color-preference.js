const isDarkMode = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

const runColorMode = fn => {
  if (!window.matchMedia) { return; }

  const query = window.matchMedia('(prefers-color-scheme: dark)');

  fn(query.matches);

  query.addEventListener('change', event => fn(event.matches));
};

const setColorMode = () => {
  runColorMode(isDarkMode => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  });
};

{% if user.is_authenticated and user.profile.color_preference == 'auto' or not user.is_authenticated %}
setColorMode();
{% endif %}
