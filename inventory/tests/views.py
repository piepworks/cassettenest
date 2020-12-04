import datetime
import io
import csv
import pytz
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker
from inventory.models import Roll, Camera, CameraBack, Project, Journal
from inventory.utils import status_number

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

    def test_export_camera_backs(self):
        baker.make(CameraBack, camera=baker.make(Camera, owner=self.user))
        baker.make(CameraBack, camera=baker.make(Camera, owner=self.user))

        response = self.client.get(reverse('export-camera-backs'))
        reader = csv.reader(io.StringIO(response.content.decode('UTF-8')))
        # Disregard the header row.
        next(reader)
        rows = sum(1 for row in reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows, 2)

    def test_export_projects(self):
        project1 = baker.make(Project, owner=self.user)
        project2 = baker.make(Project, owner=self.user)
        baker.make(Roll, project=project1, owner=self.user)
        project1.cameras.add(baker.make(Camera, owner=self.user))

        response = self.client.get(reverse('export-projects'))
        reader = csv.reader(io.StringIO(response.content.decode('UTF-8')))
        # Disregard the header row.
        next(reader)
        rows = sum(1 for row in reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows, 2)

    def test_export_journals(self):
        baker.make(Journal, roll=baker.make(Roll, owner=self.user))
        baker.make(Journal, roll=baker.make(Roll, owner=self.user))

        response = self.client.get(reverse('export-journals'))
        reader = csv.reader(io.StringIO(response.content.decode('UTF-8')))
        # Disregard the header row.
        next(reader)
        rows = sum(1 for row in reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows, 2)


@freeze_time(datetime.datetime.now())
class ImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = datetime.datetime.now().date()
        cls.tz_yesterday = timezone.make_aware(
            datetime.datetime.now() - datetime.timedelta(days=1),
            timezone=pytz.timezone('UTC'),
        )
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

    def test_import_rolls_failure(self):
        response = self.client.post(
            reverse('import-rolls'),
            data={'csv': 'Nothing.'},
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Nope.', messages)

    def test_import_rolls_success(self):
        camera = baker.make(Camera, owner=self.user)
        project = baker.make(Project, owner=self.user)
        roll = baker.make(
            Roll,
            owner=self.user,
            camera=camera,
            camera_back=baker.make(CameraBack, camera=camera),
            project=project,
            started_on=self.today,
            # Don’t set ended_on manually, let the model’s save method do it.
            status=status_number('shot'),
        )
        self.assertEqual(Roll.objects.filter(owner=self.user).count(), 1)

        # Set created_at and updated_at to yesterday so we can be sure the
        # import doesn’t change it.
        Roll.objects.filter(owner=self.user).update(
            created_at=self.tz_yesterday,
            updated_at=self.tz_yesterday,
        )

        # First, export.
        response1 = self.client.get(reverse('export-rolls'))
        reader = csv.reader(io.StringIO(response1.content.decode('UTF-8')))
        next(reader)  # Disregard the header row.
        rows = sum(1 for row in reader)
        self.assertEqual(rows, 1)
        self.assertEquals(
            response1.get('Content-Disposition'),
            'attachment; filename="rolls.csv"'
        )

        # Next, delete.
        roll.delete()
        self.assertEqual(Roll.objects.filter(owner=self.user).count(), 0)

        # Then import from our export.
        response2 = self.client.post(
            reverse('import-rolls'),
            data={'csv': SimpleUploadedFile('rolls.csv', response1.content)},
        )
        messages = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Imported 1 roll.', messages)
        rolls = Roll.objects.filter(owner=self.user)
        self.assertEqual(rolls.count(), 1)

        # Make sure we set `created_at` and `update_at` from the csv.
        self.assertEqual(rolls[0].created_at, self.tz_yesterday)
        self.assertEqual(rolls[0].updated_at, self.tz_yesterday)

    def test_import_cameras_failure(self):
        response = self.client.post(
            reverse('import-cameras'),
            data={'csv': 'Nothing.'},
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Nope.', messages)

    def test_import_cameras_success(self):
        camera = baker.make(Camera, owner=self.user)
        self.assertEqual(Camera.objects.filter(owner=self.user).count(), 1)

        # Set created_at and updated_at to yesterday so we can be sure the
        # import doesn’t change it.
        Camera.objects.filter(owner=self.user).update(
            created_at=self.tz_yesterday,
            updated_at=self.tz_yesterday,
        )

        # First, export.
        response1 = self.client.get(reverse('export-cameras'))
        reader = csv.reader(io.StringIO(response1.content.decode('UTF-8')))
        next(reader)  # Disregard the header row.
        rows = sum(1 for row in reader)
        self.assertEqual(rows, 1)
        self.assertEquals(
            response1.get('Content-Disposition'),
            'attachment; filename="cameras.csv"'
        )

        # Next, delete.
        camera.delete()
        self.assertEqual(Camera.objects.filter(owner=self.user).count(), 0)

        # Then import from our export.
        response2 = self.client.post(
            reverse('import-cameras'),
            data={'csv': SimpleUploadedFile('cameras.csv', response1.content)},
        )
        messages = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Imported 1 camera.', messages)
        cameras = Camera.objects.filter(owner=self.user)
        self.assertEqual(cameras.count(), 1)

        # Make sure we set `created_at` and `update_at` from the csv.
        self.assertEqual(cameras[0].created_at, self.tz_yesterday)
        self.assertEqual(cameras[0].updated_at, self.tz_yesterday)
