const stripe = Stripe('{{ stripe_public_key }}');
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

$('.subscribe').click(e => {
    const price = $(e.target).data('price');
    const checkoutSessionURL = `{% url 'checkout-session' price='temp' %}`.replace('temp', price);

    // Get checkout session ID.
    fetch(checkoutSessionURL)
        .then(result => result.json())
        .then(data => stripe.redirectToCheckout({sessionId: data.sessionId}))
        .then(res => {
            console.log('res', res);
        });
});

$('.manage-subscription').click(() => {
    const request = new Request(
        `{% url 'stripe-portal' %}`,
        {
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        },
    );
    fetch(request, {
        method: 'POST',
        mode: 'same-origin',
        body: JSON.stringify({}),
    })
        .then(response => response.json())
        .then(data => {
            window.location.href = data.url;
        })
        .catch(error => {
            console.error('Error:', error);
        });
});
