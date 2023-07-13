# Adapted from:
# https://github.com/paddle-python/dj-paddle/blob/f476110024cd0a4d0df6660fbdc2702442c96d6e/djpaddle/utils.py
# and
# https://developer.paddle.com/webhook-reference/verifying-webhooks

import base64
import collections

import phpserialize
from Crypto.PublicKey import RSA

try:
    from Crypto.Hash import SHA1
except ImportError:  # pragma: no cover
    from Crypto.Hash import SHA as SHA1

try:
    from Crypto.Signature import PKCS1_v1_5
except ImportError:  # pragma: no cover
    from Crypto.Signature import pkcs1_15 as PKCS1_v1_5

from django.conf import settings
from ipaddress import ip_address, ip_network

from .utils import send_email_to_trey

supported_webhooks = (
    "subscription_created",
    "subscription_updated",
    "subscription_cancelled",
    "subscription_payment_succeeded",
    "subscription_payment_failed",
    "subscription_payment_refunded",
)

valid_plans = {
    settings.PADDLE_STANDARD_ANNUAL: "Standard (annual)",
    settings.PADDLE_STANDARD_MONTHLY: "Standard (monthly)",
    settings.PADDLE_AWESOME_ANNUAL: "Awesome (annual)",
}


def paddle_plan_name(plan_id):
    return valid_plans[str(plan_id)]


def is_valid_plan(plan_id):
    return str(plan_id) in valid_plans


def is_valid_webhook(payload):
    # Convert key from PEM to DER - Strip the first and last lines and newlines, and decode
    public_key_encoded = settings.PADDLE_PUBLIC_KEY[26:-25].replace("\n", "")
    public_key_der = base64.b64decode(public_key_encoded)

    # payload represents all of the POST fields sent with the request
    # Get the p_signature parameter & base64 decode it.
    signature = payload["p_signature"]

    # Remove the p_signature parameter
    del payload["p_signature"]

    # Ensure all the data fields are strings
    for field in payload:
        payload[field] = str(payload[field])

    # Sort the data
    sorted_data = collections.OrderedDict(sorted(payload.items()))

    # and serialize the fields
    serialized_data = phpserialize.dumps(sorted_data)

    # verify the data
    key = RSA.importKey(public_key_der)
    digest = SHA1.new()
    digest.update(serialized_data)
    verifier = PKCS1_v1_5.new(key)
    signature = base64.b64decode(signature)

    return verifier.verify(digest, signature)


def is_valid_ip_address(forwarded_for):
    # https://developer.paddle.com/webhook-reference/webhooks-security

    client_ip_address = ip_address(forwarded_for.split(",")[0])

    if settings.PADDLE_LIVE_MODE == 0:
        allow_list = [
            "34.194.127.46",
            "54.234.237.108",
            "3.208.120.145",
            "44.226.236.210",
            "44.241.183.62",
            "100.20.172.113",
        ]
    else:
        allow_list = [
            "34.232.58.13",
            "34.195.105.136",
            "34.237.3.244",
            "35.155.119.135",
            "52.11.166.252",
            "34.212.5.7",
        ]

    for valid_ip in allow_list:
        if client_ip_address in ip_network(valid_ip):
            return True
    else:
        return False


def update_subscription(alert_name, user, payload):
    user.profile.paddle_user_id = payload.get("user_id")
    user.profile.paddle_subscription_id = payload.get("subscription_id")
    user.profile.paddle_subscription_plan_id = payload.get("subscription_plan_id")
    user.profile.subscription_status = payload.get("status")
    if payload.get("update_url"):
        user.profile.paddle_update_url = payload.get("update_url")
    if payload.get("cancel_url"):
        user.profile.paddle_cancel_url = payload.get("cancel_url")
    if payload.get("cancellation_effective_date"):
        user.profile.paddle_cancellation_date = payload.get(
            "cancellation_effective_date"
        )

    user_display = f"{user.username} / {user.email}"
    plan_name = paddle_plan_name(user.profile.paddle_subscription_plan_id)

    if alert_name == "subscription_created":
        subject = "New Cassette Nest subscription!"
        message = f"{user_display} subscribed to the {plan_name} plan!"

    elif alert_name == "subscription_updated":
        old_plan = paddle_plan_name(payload.get("old_subscription_plan_id"))

        subject = "Cassette Nest subscription updated"

        if old_plan != plan_name:
            message = f"{user_display} updated their subscription from {old_plan} to {plan_name}."
        else:
            message = (
                f"{user_display} updated something on their {plan_name} subscription."
            )

    elif alert_name == "subscription_cancelled":
        subject = "Cassette Nest subscription cancellation. :("
        message = f"{user_display} cancelled their {plan_name} subscription."

    elif alert_name == "subscription_payment_succeeded":
        subject = "Cassette Nest payment succeeded!"
        message = (
            f"{user_display} successfully paid for their {plan_name} subscription."
        )

    elif alert_name == "subscription_payment_failed":
        subject = "Cassette Nest payment failure"
        message = (
            f"{user_display} is having trouble with their {plan_name} subscription."
        )

    elif alert_name == "subscription_payment_refunded":
        subject = "Cassette Nest payment refund"
        message = f"{user_display} got a refund for their {plan_name} subscription."

    user.save()

    send_email_to_trey(
        subject=subject,
        message=message,
    )
