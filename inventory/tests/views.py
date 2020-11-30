from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
staticfiles_storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
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


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class PatternsTests(TestCase):
    def test_patterns_page(self):
        response = Client().get(reverse('patterns'))

        self.assertEqual(response.status_code, 200)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_settings_page(self):
        response = self.client.get(reverse('settings'))

        self.assertEqual(response.status_code, 200)

    def test_settings_update(self):
        response = self.client.post(reverse('settings'), data={
            'username': self.username,
            'first_name': 'Frank',
            'last_name': 'Poole',
            'email': 'frank@example.com',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Settings updated!', messages)

    def test_settings_update_error(self):
        response = self.client.post(reverse('settings'), data={
            'first_name': 'Frank',
            'last_name': 'Poole',
            'email': 'frank@example.com',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Username: This field is required.', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RegisterTests(TestCase):
    def test_registration_page(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an account to continue.', html=True)

    def test_registering_new_user(self):
        username = 'testtest'
        password = 'secret1234'
        email = 'test@example.com'

        response = self.client.post(reverse('register'), data={
            'username': username,
            'password1': password,
            'password2': password,
            'email': email,
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.wsgi_request.user.username, username)

    def test_registration_form_error(self):
        response = self.client.post(reverse('register'), data={
            'username': 'test',
            'password1': 'password',
            'password2': 'password',
            'email': 'test@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This password is too common.', html=True)
