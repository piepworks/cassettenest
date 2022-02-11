module.exports = {
  // darkMode: 'class',
  content: [
    // (BASE_DIR/templates)
    '../../templates/**/*.html',

    // (BASE_DIR/<any_app_name>/templates)
    '../../**/templates/**/*.html',
    '../../**/templates/**/*.js',
    '../../**/templates/**/*.svg',
  ],
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
