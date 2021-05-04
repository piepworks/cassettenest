const $progressiveFields = $('.c-field--progressive');

function progressiveLinkSetup(element) {
    const $element = $(element);
    const $progressiveLink = $(`<a>${$element.data('progressive-text')}</a>`);
    let primaryField;

    if ($element.hasClass('c-field--progressive-primary')) {
        primaryField = true;
    } else {
        $element.hide();
        const oldLabel = $element.find('label').text();
        const newLabel = oldLabel.replace('Or', '').replace('.', '');

        // TODO: just change the label of the secondary field to the label
        // of the primary field. The only thing differentiating them could just
        // be the JS-clicky text.

        $element.find('label').text(newLabel.substring(1)[0].toUpperCase() + newLabel.substring(2));
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
