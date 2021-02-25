function checkoutClosed(data) {
    console.log(data);
    console.log(`data.user.id: ${data.user.id}`);
    console.log('Your purchase has been cancelled, we hope to see you again soon!');
}

function checkoutComplete(data) {
    console.log(data);
    console.log('Thanks for your purchase.');

    // Post to an endpoint and update the following items:
    // Actually, I may need to rely on the webhook.
    // https://developer.paddle.com/webhook-reference/subscription-alerts/subscription-created
    // https://developer.paddle.com/webhook-reference/subscription-alerts/subscription-updated

    // - paddle_user_id
    // - paddle_subscription_id
    // - paddle_subscription_plan_id
    // - paddle_cancel_url
    // - paddle_update_url
}

function openCheckout(product) {
    Paddle.Checkout.open({
        product: product,
        email: '{{ user.email }}',
        passthrough: '{\"cn_user_id\": \"{{ user.id }}\" }',
        successCallback: checkoutComplete,
        closeCallback: checkoutClosed,
    });
}

$('.paddle').click(e => {
    openCheckout($(e.target).data('product'));
});
