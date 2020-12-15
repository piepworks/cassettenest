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
from inventory.utils import status_number, bulk_status_next_keys, status_description

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
        status = 'shot'
        response = self.client.get(reverse('logbook'), data={
            'status': status,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, status_description(status), html=True)
        self.assertEqual(response.context['bulk_status_next'], bulk_status_next_keys[status])
        self.assertEqual(response.context['status_counts']['shot'], 1)

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

    def test_js_needed(self):
        response = self.client.get(reverse('logbook'))

        self.assertEqual(response.context['js_needed'], True)


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

    def test_import_camera_backs_failure(self):
        response = self.client.post(
            reverse('import-camera-backs'),
            data={'csv': 'Nothing.'},
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Nope.', messages)

    def test_import_camera_backs_success(self):
        camera_back = baker.make(CameraBack, camera=baker.make(Camera, owner=self.user))
        self.assertEqual(CameraBack.objects.filter(camera__owner=self.user).count(), 1)

        # Set created_at and updated_at to yesterday so we can be sure the
        # import doesn’t change it.
        CameraBack.objects.filter(camera__owner=self.user).update(
            created_at=self.tz_yesterday,
            updated_at=self.tz_yesterday,
        )

        # First, export.
        response1 = self.client.get(reverse('export-camera-backs'))
        reader = csv.reader(io.StringIO(response1.content.decode('UTF-8')))
        next(reader)  # Disregard the header row.
        rows = sum(1 for row in reader)
        self.assertEqual(rows, 1)
        self.assertEquals(
            response1.get('Content-Disposition'),
            'attachment; filename="camera-backs.csv"'
        )

        # Next, delete.
        camera_back.delete()
        self.assertEqual(CameraBack.objects.filter(camera__owner=self.user).count(), 0)

        # Then import from our export.
        response2 = self.client.post(
            reverse('import-camera-backs'),
            data={'csv': SimpleUploadedFile('camera-backs.csv', response1.content)},
        )
        messages = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Imported 1 camera back.', messages)
        camera_backs = CameraBack.objects.filter(camera__owner=self.user)
        self.assertEqual(camera_backs.count(), 1)

        # Make sure we set `created_at` and `update_at` from the csv.
        self.assertEqual(camera_backs[0].created_at, self.tz_yesterday)
        self.assertEqual(camera_backs[0].updated_at, self.tz_yesterday)

    def test_import_projects_failure(self):
        response = self.client.post(
            reverse('import-projects'),
            data={'csv': 'Nothing.'},
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Nope.', messages)

    def test_import_projects_success(self):
        project = baker.make(Project, owner=self.user)
        baker.make(Roll, project=project, owner=self.user)
        project.cameras.add(baker.make(Camera, owner=self.user))
        self.assertEqual(Project.objects.filter(owner=self.user).count(), 1)

        # Set created_at and updated_at to yesterday so we can be sure the
        # import doesn’t change it.
        Project.objects.filter(owner=self.user).update(
            created_at=self.tz_yesterday,
            updated_at=self.tz_yesterday,
        )

        # First, export.
        response1 = self.client.get(reverse('export-projects'))
        reader = csv.reader(io.StringIO(response1.content.decode('UTF-8')))
        next(reader)  # Disregard the header row.
        rows = sum(1 for row in reader)
        self.assertEqual(rows, 1)
        self.assertEquals(
            response1.get('Content-Disposition'),
            'attachment; filename="projects.csv"'
        )

        # Next, delete.
        project.delete()
        self.assertEqual(Project.objects.filter(owner=self.user).count(), 0)

        # Then import from our export.
        response2 = self.client.post(
            reverse('import-projects'),
            data={'csv': SimpleUploadedFile('projects.csv', response1.content)},
        )
        messages = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Imported 1 project.', messages)
        projects = Project.objects.filter(owner=self.user)
        self.assertEqual(projects.count(), 1)

        # Make sure we set `created_at` and `update_at` from the csv.
        self.assertEqual(projects[0].created_at, self.tz_yesterday)
        self.assertEqual(projects[0].updated_at, self.tz_yesterday)

    def test_import_journals_failure(self):
        response = self.client.post(
            reverse('import-journals'),
            data={'csv': 'Nothing.'},
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Nope.', messages)

    def test_import_journals_success(self):
        journal = baker.make(Journal, roll=baker.make(Roll, owner=self.user))
        self.assertEqual(Journal.objects.filter(roll__owner=self.user).count(), 1)

        # Set created_at and updated_at to yesterday so we can be sure the
        # import doesn’t change it.
        Journal.objects.filter(roll__owner=self.user).update(
            created_at=self.tz_yesterday,
            updated_at=self.tz_yesterday,
        )

        # First, export.
        response1 = self.client.get(reverse('export-journals'))
        reader = csv.reader(io.StringIO(response1.content.decode('UTF-8')))
        next(reader)  # Disregard the header row.
        rows = sum(1 for row in reader)
        self.assertEqual(rows, 1)
        self.assertEquals(
            response1.get('Content-Disposition'),
            'attachment; filename="journals.csv"'
        )

        # Next, delete.
        journal.delete()
        self.assertEqual(Journal.objects.filter(roll__owner=self.user).count(), 0)

        # Then import from our export.
        response2 = self.client.post(
            reverse('import-journals'),
            data={'csv': SimpleUploadedFile('journals.csv', response1.content)},
        )
        messages = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Imported 1 journal.', messages)
        journals = Journal.objects.filter(roll__owner=self.user)
        self.assertEqual(journals.count(), 1)

        # Make sure we set `created_at` and `update_at` from the csv.
        self.assertEqual(journals[0].created_at, self.tz_yesterday)
        self.assertEqual(journals[0].updated_at, self.tz_yesterday)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class JournalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.roll = baker.make(Roll, owner=cls.user)
        cls.entry = baker.make(Journal, roll=cls.roll)

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_journal_edit_get(self):
        response = self.client.get(reverse('roll-journal-edit', args=(self.roll.id, self.entry.id)))

        self.assertEqual(response.status_code, 200)

    def test_journal_edit_post(self):
        today = datetime.datetime.now().date()
        yesterday = today - datetime.timedelta(days=1)

        response1 = self.client.post(
            reverse('roll-journal-edit', args=(self.roll.id, self.entry.id)),
            data={
                'date': today,
                'notes': 'What noise annoys a noisy oyster?',
                'frame': 3,
            }
        )
        messages1 = [m.message for m in get_messages(response1.wsgi_request)]

        self.assertRedirects(response1, reverse('roll-journal-detail', args=(self.roll.id, self.entry.id)))
        self.assertIn('Journal entry updated.', messages1)

        # Try to save another entry with the same date as an existing entry.
        entry2 = baker.make(Journal, roll=self.roll, date=yesterday)
        response2 = self.client.post(
            reverse('roll-journal-edit', args=(self.roll.id, entry2.id)),
            data={
                'date': today,
                'notes': 'This entry will not work.',
                'frame': 5,
            }
        )
        messages2 = [m.message for m in get_messages(response2.wsgi_request)]

        self.assertEqual(response2.status_code, 302)
        self.assertIn('Only one entry per date per roll.', messages2)

    def test_journal_edit_post_invalid(self):
        # Try submitting an invalid form.
        # If I put this with the rest of the tests above,
        # I get a `TransactionManagementError`. So here’s a new test.
        roll = baker.make(Roll, owner=self.user)
        entry = baker.make(Journal, roll=roll)
        response = self.client.post(
            reverse('roll-journal-edit', args=(roll.id, entry.id)),
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Something is not right.', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class ReadyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_empty_ready_page(self):
        response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No rolls ready to process.', html=True)

    def test_ready_page_with_a_roll(self):
        baker.make(
            Roll,
            owner=self.user,
            status=status_number('shot'),
            started_on=self.today,
            camera=baker.make(Camera),
        )
        response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have 1 roll ready to process.', html=True)

    def test_js_needed(self):
        response = self.client.get(reverse('ready'))

        self.assertEqual(response.context['js_needed'], True)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RollsUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        cls.camera = baker.make(Camera, owner=cls.user)
        baker.make(
            Roll,
            owner=cls.user,
            status=status_number('processing'),
            started_on=cls.today,
            camera=cls.camera,
        )
        baker.make(
            Roll,
            owner=cls.user,
            status=status_number('processing'),
            started_on=cls.today,
            camera=cls.camera,
        )

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_update_rolls_to_processed(self):
        rolls = Roll.objects.filter(owner=self.user, status=status_number('processing'))
        roll_ids = list(roll.id for roll in rolls)

        response = self.client.post(reverse('rolls-update'), data={
            'current_status': 'processing',
            'updated_status': bulk_status_next_keys['processing'],
            'roll': roll_ids,
            'lab': 'Home',
            'scanner': 'Epson V600',
            'notes_on_development': 'I enjoy this tedium.',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('2 rolls updated from processing to processed!', messages)

    def test_update_rolls_errors(self):
        # Neither of these statuses are are `bulk_status`es.
        response = self.client.post(reverse('rolls-update'), data={
            'current_status': 'storage',
            'updated_status': 'loaded',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Something is amiss.', messages)
