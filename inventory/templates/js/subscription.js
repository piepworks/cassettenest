const stripe = Stripe('{{ stripe_public_key }}');

$('.subscribe').click(e => {
    const price = $(e.target).data('price');
    const checkoutSessionURL = `{% url 'checkout-session' price='temp' %}`.replace('temp', price);

    // Get checkout session ID.
    fetch(checkoutSessionURL)
        .then((result) => { return result.json(); })
        .then((data) => {
            console.log('data', data);
            // Redirect to Stripe Checkout.
            return stripe.redirectToCheckout({sessionId: data.sessionId});
        })
        .then((res) => {
            console.log('res', res);
        });
});

$('.manage-subscription').click(e => {
    console.log('e', e);
});
