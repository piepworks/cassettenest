module.exports = {
  darkMode: 'class',
  content: [
    '**/templates/**/*.{html,js,svg}',
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          light: '#f5d327',
          DEFAULT: '#f3ba4c',
        }
      },
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
