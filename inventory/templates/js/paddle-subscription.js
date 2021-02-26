function openCheckout(product) {
    Paddle.Checkout.open({
        product: product,
        email: '{{ user.email }}',
        passthrough: '{{ user.id }}',
        success: `${window.location.protocol}//${window.location.host}{% url 'subscription-created' %}?plan=${product}`,
    });
}

$('.paddle').click(e => {
    openCheckout($(e.target).data('product'));
});
