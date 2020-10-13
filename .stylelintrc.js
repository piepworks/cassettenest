module.exports = {
    'extends': 'stylelint-config-standard',
    'rules': {
        'indentation': 4,
        'string-quotes': 'single',
        'at-rule-no-unknown': null,
        'declaration-empty-line-before': 'never',
        'no-descending-specificity': null,
    },
    'ignoreFiles': 'inventory/static/inventory/scss/vendor/**',
};
