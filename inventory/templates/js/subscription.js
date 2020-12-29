// eslint-disable-next-line no-undef
const stripe = Stripe('{{ stripe_public_key }}');

console.log('stripe', stripe);

$('button').click((e) => {
    console.log(`price id: ${$(e.target).data('price')}`);
});
