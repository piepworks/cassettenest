module.exports = {
  'extends': 'stylelint-config-standard',
  'rules': {
    'indentation': 2,
    'string-quotes': 'single',
    'at-rule-no-unknown': null,
    'declaration-empty-line-before': 'never',
    'no-descending-specificity': null,
  },
  'ignoreFiles': ['static/scss/vendor/**', 'theme/static/css/dist/**'],
};
