function openCheckout(product) {
    Paddle.Checkout.open({
        product: product,
        email: '{{ user.email }}',
        passthrough: '{{ user.id }}',
        success: `${window.location.protocol}//${window.location.host}{% url 'subscription-created' %}?plan=${product}`,
    });
}

$('.paddle-subscribe').click(e => {
    openCheckout($(e.target).data('product'));
});

$('.paddle-update').click(() => {
    Paddle.Checkout.open({
        override: '{{ user.profile.paddle_update_url|safe }}',
    });
});

$('.paddle-cancel').click(() => {
    Paddle.Checkout.open({
        override: '{{ user.profile.paddle_cancel_url|safe }}',
    });
});
