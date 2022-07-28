module.exports = {
  // darkMode: 'class',
  content: [
    '**/templates/**/*.{html,js,svg}',
  ],
  theme: {
    extend: {
      screens: {
        'tall': { 'raw': '(min-height: 450px)' }
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
