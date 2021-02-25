function openCheckout(product, name) {
    Paddle.Checkout.open({
        product: product,
        email: '{{ user.email }}',
        passthrough: '{{ user.id }}',
        success: `${window.location.protocol}//${window.location.host}{% url 'subscription-created' %}?plan=${name}`,
    });
}

$('.paddle').click(e => {
    const product = $(e.target).data('product');
    const name = $(e.target).data('name');

    openCheckout(product, name);
});
