const stripe = Stripe('{{ stripe_public_key }}');
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function checkoutClosed(data) {
    console.log(data);
    console.log('Your purchase has been cancelled, we hope to see you again soon!');
}

function checkoutComplete(data) {
    console.log(data);
    console.log('Thanks for your purchase.');
}

function openCheckout(product) {
    Paddle.Checkout.open({
        product: product,
        email: '{{ user.email }}',
        successCallback: checkoutComplete,
        closeCallback: checkoutClosed,
    });
}

$('.paddle').click(e => {
    openCheckout($(e.target).data('product'));
});

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
