import pytest
from pyquery import PyQuery as pq
from model_bakery import baker
from django import urls
from django.contrib.auth.models import User
from django.test import override_settings
from inventory.models import Stock, Film, Roll, Camera

staticfiles_storage = {
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
}


@override_settings(STORAGES=staticfiles_storage)
@pytest.mark.django_db
def test_camera_or_back_load_form(client):
    user = User.objects.create_user("test-user")
    roll = baker.make(Roll, film=baker.make(Film, stock=baker.make(Stock)), owner=user)
    camera = baker.make(Camera, owner=user)
    client.force_login(user)

    response = client.get(urls.reverse("camera-load", args=(camera.id,)))
    d = pq(response.content)

    assert response.status_code == 200
    assert d(f"#id_film option[value='{roll.film.id}']") != []
