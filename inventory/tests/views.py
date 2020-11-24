from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class IndexTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/'
        self.view = 'login'
        self.username = 'test'
        self.password = 'secret'

    def test_logged_out(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f'{reverse(self.view)}?next={self.url}')

    def test_logged_in(self):
        user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        self.client.login(
            username=self.username,
            password=self.password,
        )
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
