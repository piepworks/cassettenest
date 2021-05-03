const $progressiveFields = $('.c-field--progressive');

function progressiveLinkSetup(element) {
    const $progressiveLink = $(`<a>${$(element).data('progressive-text')}</a>`);
    const $element = $(element);
    let clickEvent;

    $progressiveLink.click(() => {
        if ($element.hasClass('c-field--progressive-primary')) {
            clickEvent = 'primary click!';
        } else {
            clickEvent = 'secondary click!';
        }

        console.log('clickEvent', clickEvent);
    });

    $element.find('.js-link').append($progressiveLink);
}

$progressiveFields.each((index, element) => progressiveLinkSetup(element));
