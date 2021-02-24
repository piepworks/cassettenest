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


def is_valid_webhook(payload):
    # Convert key from PEM to DER - Strip the first and last lines and newlines, and decode
    public_key_encoded = settings.PADDLE_PUBLIC_KEY[26:-25].replace('\n', '')
    public_key_der = base64.b64decode(public_key_encoded)

    # payload represents all of the POST fields sent with the request
    # Get the p_signature parameter & base64 decode it.
    signature = payload['p_signature']

    # Remove the p_signature parameter
    del payload['p_signature']

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

    client_ip_address = ip_address(forwarded_for)

    if settings.PADDLE_LIVE_MODE == 0:
        allow_list = [
            '34.194.127.46',
            '54.234.237.108',
            '3.208.120.145',
        ]
    else:
        allow_list = [
            '34.232.58.13',
            '34.195.105.136',
            '34.237.3.244',
        ]

    for valid_ip in allow_list:
        if client_ip_address in ip_network(valid_ip):
            return True
    else:
        return False
