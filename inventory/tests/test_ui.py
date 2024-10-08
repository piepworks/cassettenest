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
    test_server.get_by_role("link", name="create an account").click()
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

    header = test_server.locator("h1")
    expect(header).to_contain_text(
        "Registration submitted!Check your email for a confirmation link."
    )
