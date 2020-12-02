import datetime
import io
import csv
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from inventory.models import Roll, Camera
from inventory.utils import status_number
from model_bakery import baker

staticfiles_storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class IndexTests(TestCase):
    def setUp(self):
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
        response = self.client.get(reverse('patterns'))

        self.assertEqual(response.status_code, 200)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class InventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        baker.make(Roll, owner=cls.user)

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_restricted(self):
        response = self.client.get(reverse('inventory'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inventory', html=True)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class LogbookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        baker.make(
            Roll,
            owner=cls.user,
            status=status_number('shot'),
            started_on=cls.today,
            camera=baker.make(Camera),
        )

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_main_logbook_page(self):
        response = self.client.get(reverse('logbook'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Logbook', html=True)

    def test_status_logbook_page(self):
        response = self.client.get(reverse('logbook'), data={
            'status': 'shot',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ready to be developed.', html=True)

    def test_storage_status_logbook_redirect(self):
        response = self.client.get(reverse('logbook'), data={
            'status': 'storage',
        })

        self.assertEqual(response.status_code, 302)

    def test_year_logbook_page(self):
        response = self.client.get(reverse('logbook'), data={
            'year': self.today.year,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['year'], str(self.today.year))
        self.assertEqual(len(response.context['rolls']), 1)


class ExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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

    def test_export_rolls(self):
        baker.make(Roll, owner=self.user)
        baker.make(Roll, owner=self.user)

        response = self.client.get(reverse('export-rolls'))
        reader = csv.reader(io.StringIO(response.content.decode('UTF-8')))
        # Disregard the header row.
        next(reader)
        rows = sum(1 for row in reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows, 2)

    def test_export_cameras(self):
        baker.make(Camera, owner=self.user)
        baker.make(Camera, owner=self.user)

        response = self.client.get(reverse('export-cameras'))
        reader = csv.reader(io.StringIO(response.content.decode('UTF-8')))
        # Disregard the header row.
        next(reader)
        rows = sum(1 for row in reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows, 2)
