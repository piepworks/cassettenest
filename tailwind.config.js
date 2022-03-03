module.exports = {
  // darkMode: 'class',
  content: [
    '**/templates/**/*.html',
    '**/templates/**/*.js',
    '**/templates/**/*.svg',
  ],
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
