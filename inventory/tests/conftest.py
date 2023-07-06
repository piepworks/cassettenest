import os
import pytest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "True")


@pytest.fixture()
def test_server(page, live_server):
    page.goto(live_server.url)
    return page
