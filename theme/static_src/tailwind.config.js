const colors = require('tailwindcss/colors');

module.exports = {
  content: [
    // (BASE_DIR/templates)
    '../../templates/**/*.html',

    // (BASE_DIR/<any_app_name>/templates)
    '../../**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        gray: colors.stone,
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
