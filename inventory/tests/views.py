from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class IndexTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.login_url = reverse('login')
        self.username = 'test'
        self.password = 'secret'

    def test_logged_out(self):
        response = self.client.get(self.index_url)

        self.assertRedirects(response, f'{self.login_url}?next={self.index_url}')

    def test_logged_in(self):
        user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        self.client.login(
            username=self.username,
            password=self.password,
        )
        response = self.client.get(self.index_url)

        self.assertEqual(response.status_code, 200)


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class Patternstests(TestCase):
    def test_patterns_page(self):
        response = Client().get(reverse('patterns'))

        self.assertEqual(response.status_code, 200)
