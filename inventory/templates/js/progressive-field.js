const $progressiveFields = $('.c-field--progressive');

function progressiveLinkSetup(element) {
    const $element = $(element);
    const $progressiveLink = $(`<a>${$element.data('progressive-text')}</a>`);
    let primaryField;

    if ($element.hasClass('c-field--progressive-primary')) {
        primaryField = true;
    } else {
        const primaryLabel = $element.prev('.c-field--progressive').data('label');

        $element.hide();
        $element.find('label').text(primaryLabel);
    }

    $progressiveLink.click(() => {
        $element.hide();

        if (primaryField) {
            $element.next('.c-field--progressive').show();
        } else {
            $element.prev('.c-field--progressive').show();
        }
    });

    $element.find('.js-link').append($progressiveLink);
}

$progressiveFields.each((index, element) => progressiveLinkSetup(element));
