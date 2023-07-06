import re
from playwright.sync_api import expect


def test_login_page(test_server):
    expect(test_server).to_have_title(re.compile("Log in / Cassette Nest"))
