import re
import pytest
import random
import string
from playwright.sync_api import expect


@pytest.mark.playwright()
def test_login_page(test_server):
    expect(test_server).to_have_title(re.compile("Log in / Cassette Nest"))


@pytest.mark.playwright()
def test_create_account(test_server):
    test_server.get_by_role("link", name="start your 14-day free trial").click()
    username = "".join(random.choice(string.ascii_letters) for i in range(5))
    test_server.get_by_label("Username").fill(username)
    test_server.get_by_label("Email").fill(f"{username}@example.com")
    password = "".join(
        random.choice(string.ascii_letters + string.digits + string.punctuation)
        for i in range(12)
    )
    test_server.get_by_label("Password", exact=True).fill(password)
    test_server.get_by_label("Password confirmation").fill(password)
    test_server.get_by_role("button", name="Create your account").click()

    subscription_banner = test_server.locator(".subscription-banner")
    expect(subscription_banner).to_be_in_viewport()

    onboarding = test_server.locator(".onboarding")
    expect(onboarding).to_contain_text("Welcome to Cassette Nest! Let’s get started:")


# TODO: test film stock dropdown htmx stuff
