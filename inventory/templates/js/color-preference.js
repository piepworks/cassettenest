window.isDarkMode = () => window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

window.cnDarkMode = {
  run: function (fn) {
    if (!window.matchMedia) { return; }
    const query = window.matchMedia('(prefers-color-scheme: dark)');
    fn(query.matches);
    query.addEventListener('change', event => fn(event.matches));
  },

  set: function() {
    this.run(isDarkMode => {
      if (isDarkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    });
  },
};

/* (Hide this Django code from ESLint)
{% if user.is_authenticated and user.profile.color_preference == 'auto' or not user.is_authenticated %}
*/
window.cnDarkMode.set();
/*
{% endif %}
*/
