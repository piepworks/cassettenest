module.exports = {
  extends: 'stylelint-config-standard',
  rules: {
    'declaration-empty-line-before': 'never',
    'no-descending-specificity': null,
    // Tailwind-related rules:
    // -----------------------
    'function-no-unknown': [true, { ignoreFunctions: ['theme'] }],
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen',
        ],
      },
    ],
    'at-rule-empty-line-before': null,
    'value-keyword-case': null,
    'at-rule-no-deprecated': null,
    'declaration-property-value-no-unknown': null,
    // -----------------------
  },
  ignoreFiles: ['static/tailwind.css'],
};
