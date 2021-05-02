const $primaryFields = $('.c-field--progressive-primary');
const $secondaryFields = $('.c-field--progressive').not('.c-field--progressive-primary');

$primaryFields.each((index, element) =>{
    console.log('primary index', index);
    console.log('primary element', element);

    const primaryLabel = `…or enter your own ${$(element).data('label').toLowerCase()}.`;
    $(element).find('.js-link').append(`<a>${primaryLabel}</a>`);
});

$secondaryFields.each((index, element) => {
    console.log('secondary index', index);
    console.log('secondary element', element);

    const secondaryLabel = $(element).data('label').replace('Or', '…or').replace('enter your own', 'select a predefined');
    $(element).find('.js-link').append(`<a>${secondaryLabel}</a>`);
});
