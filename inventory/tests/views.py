import datetime
import io
import csv
import pytz
import logging
from unittest import mock
from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.conf import settings
from freezegun import freeze_time
from model_bakery import baker
from waffle.testutils import override_flag
from django_htmx.middleware import HtmxDetails
from inventory.views import stocks, inventory, session_sidebar
from inventory.models import Roll, Camera, CameraBack, Project, Journal, Profile, Film, Frame, Stock, Manufacturer
from inventory.utils import status_number, bulk_status_next_keys, status_description
from inventory.utils_paddle import paddle_plan_name

staticfiles_storage = 'django.contrib.staticfiles.storage.StaticFilesStorage'


# A little utility to help test HTMX requests.
# https://github.com/bigskysoftware/htmx/discussions/680#discussioncomment-1682364
def htmx_request(user=None, get_url=None, post_url=None, post_data={}, trigger=None, **kwargs):
    headers = dict(HTTP_HX_Request="true", HTTP_HX_Trigger_Name=trigger)
    if get_url is not None:
        request = RequestFactory().get(
            get_url, {x: y for x, y in kwargs.items() if y is not None}, **headers)
    if post_url is not None:
        kwargs.update(headers)
        request = RequestFactory().post(post_url, data=post_data, **kwargs)
    request.htmx = HtmxDetails(request)
    request.user = user if user else AnonymousUser()
    return request


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class IndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='test',
            password='secret',
        )

    def setUp(self):
        self.client.force_login(user=self.user)
        self.index_url = reverse('index')
        self.login_url = reverse('login')

    def test_logged_in(self):
        response = self.client.get(self.index_url)

        self.assertEqual(response.status_code, 200)

    def test_logged_out(self):
        self.client.logout()

        response = self.client.get(self.index_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.index_url}')

    def test_set_cameras_tab(self):
        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.get(f'{self.index_url}?c=1&p=0&slug=c', **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cameras'].current_tab, 1)

    def test_set_projects_tab(self):
        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.get(f'{self.index_url}?c=0&p=1&slug=p', **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['projects'].current_tab, 1)


class MarketingSiteCORSTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )

    def setUp(self):
        # Reduce the log level to avoid errors like "not found."
        logger = logging.getLogger('django.request')
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

    def tearDown(self):
        # Reset the log level back to normal.
        logger = logging.getLogger('django.request')
        logger.setLevel(self.previous_level)

    def test_logged_out(self):
        response = self.client.get(reverse('marketing-site'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b'You are not logged in.')

    def test_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('marketing-site'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'You are logged in.')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class ReminderCardTests(TestCase):
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

    def test_bw_card(self):
        roll = baker.make(
            Roll,
            film__stock=baker.make(Stock, type='bw'),
            owner=self.user,
            camera=baker.make(Camera),
        )
        roll.started_on = self.today
        roll.save()

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'type-bw')


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

    def test_plan_display(self):
        plan = settings.PADDLE_STANDARD_MONTHLY
        profile = Profile.objects.get(user=self.user)
        profile.paddle_subscription_plan_id = plan
        profile.subscription_status = 'active'
        profile.save()

        response = self.client.get(reverse('settings'))

        self.assertContains(response, f'You’re currently subscribed to the <b>{paddle_plan_name(plan)}</b> plan.')

    def test_friend_mode(self):
        profile = Profile.objects.get(user=self.user)
        profile.friend = True
        profile.save()

        response = self.client.get(reverse('settings'))
        self.assertContains(response, 'You’re a friend of Piepworks')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RegisterTests(TestCase):
    def test_registration_page(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an account', html=True)

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

    def test_registration_page_redirect(self):
        username = 'testtest'
        password = 'secret1234'

        User.objects.create_user(
            username=username,
            password=password,
        )

        self.client.login(
            username=username,
            password=password,
        )

        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)


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
        cls.inventory_url = reverse('inventory')
        baker.make(Roll, owner=cls.user, film=baker.make(Film, slug='slug', stock=baker.make(Stock)))

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_unfiltered(self):
        response = self.client.get(reverse('inventory'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inventory', html=True)
        self.assertNotContains(response, '(filtered)')

    def test_filtered(self):
        response = self.client.get(reverse('inventory') + '?format=135&type=c41')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '(35mm, C41 Color)')
        self.assertContains(response, '(filtered)')

    # HTMX / Ajax
    def test_filtered_with_htmx(self):
        response = inventory(htmx_request(
            get_url=f'{self.inventory_url}?format=135&type=c41',
            user=self.user,
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '(filtered)')


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
            film__stock=baker.make(Stock),
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
            film__stock=baker.make(Stock),
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
        self.assertEqual(
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
        self.assertEqual(
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
        self.assertEqual(
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
        self.assertEqual(
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
        self.assertEqual(
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
            film__stock=baker.make(Stock),
            owner=self.user,
            status=status_number('shot'),
            started_on=self.today,
            camera=baker.make(Camera),
        )
        response = self.client.get(reverse('ready'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have 1 roll ready to process.', html=True)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RollsAddTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.film = baker.make(Film, stock=baker.make(Stock))

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_add_rolls_page(self):
        response = self.client.get(reverse('rolls-add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add rolls to storage', html=True)

    def test_adding_rolls(self):
        response = self.client.post(reverse('rolls-add'), data={
            'film': self.film.id,
            'quantity': 2,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'Added 2 rolls of {self.film}!', messages)

    def test_adding_rolls_invalid_quantity(self):
        response = self.client.post(reverse('rolls-add'), data={
            'film': self.film.id,
            'quantity': 'fish',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Enter a valid quantity.', messages)

    def test_adding_rolls_less_than_1(self):
        response = self.client.post(reverse('rolls-add'), data={
            'film': self.film.id,
            'quantity': 0,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Enter a quantity of 1 or more.', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RollAddTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        cls.film = baker.make(Film, stock=baker.make(Stock))

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_roll_add_page(self):
        response = self.client.get(reverse('roll-add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add a roll to your&nbsp;logbook', html=True)

    def test_adding_a_roll(self):
        response = self.client.post(reverse('roll-add'), data={
            'film': self.film.id,
            'status': status_number('shot'),
            'started_on': self.today,
            'ended_on': self.today,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertTrue(f'Added a roll:' in messages[0])

    def test_adding_a_roll_and_start_another(self):
        response = self.client.post(reverse('roll-add'), data={
            'film': self.film.id,
            'status': status_number('shot'),
            'started_on': self.today,
            'ended_on': self.today,
            'another': True,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertTrue(f'Added a roll:' in messages[0])

    def test_adding_a_roll_error(self):
        response = self.client.post(reverse('roll-add'), data={})
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Please fill out the form.', messages)


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
            film__stock=baker.make(Stock),
            owner=cls.user,
            status=status_number('processing'),
            started_on=cls.today,
            camera=cls.camera,
        )
        baker.make(
            Roll,
            film__stock=baker.make(Stock),
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


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class FilmRollsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        cls.film = baker.make(Film, stock=baker.make(Stock), slug='slug')
        baker.make(Roll, film=cls.film)
        baker.make(Roll, film=cls.film)

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

        # Reduce the log level to avoid errors like "not found."
        logger = logging.getLogger('django.request')
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

    def tearDown(self):
        # Reset the log level back to normal.
        logger = logging.getLogger('django.request')
        logger.setLevel(self.previous_level)

    def test_film_rolls_with_stock(self):
        response = self.client.get(reverse('film-rolls', args=(self.film.stock.slug, self.film.format,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Storage')

    def test_personal_film_rolls_404_with_stock(self):
        film = baker.make(Film, stock=baker.make(Stock), personal=True, added_by=baker.make(User))
        response = self.client.get(reverse('film-rolls', args=(film.stock.slug, film.format,)))
        self.assertEqual(response.status_code, 404)

    def test_film_rolls_without_stock(self):
        response = self.client.get(reverse('film-slug-redirect', args=(self.film.slug,)))
        self.assertEqual(response.status_code, 302)

    def test_personal_film_rolls_404_without_stock(self):
        film = baker.make(Film, slug='private-slug', personal=True, added_by=baker.make(User))
        response = self.client.get(reverse('film-slug-redirect', args=(film.slug,)))
        self.assertEqual(response.status_code, 404)

    def test_film_rolls_with_project(self):
        project = baker.make(Project, owner=self.user)
        response = self.client.get(
            reverse(
                'film-rolls', args=(self.film.stock.slug, self.film.format,)
            ) + f'?project={project.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Viewing rolls in project')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SubscriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
            id=1,
        )

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

        # Reduce the log level to avoid errors like "not found."
        logger = logging.getLogger('django.request')
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

    def tearDown(self):
        # Reset the log level back to normal.
        logger = logging.getLogger('django.request')
        logger.setLevel(self.previous_level)

    def test_subscription_success_page(self):
        plan = settings.PADDLE_STANDARD_MONTHLY

        response = self.client.get(reverse('subscription-created') + f'?plan={plan}', follow=True)

        self.assertContains(response, f'You’re subscribed to the {paddle_plan_name(plan)} plan!')

    def test_subscription_success_page_with_incorrect_plan_id(self):
        plan = '12345'

        response = self.client.get(reverse('subscription-created') + f'?plan={plan}', follow=True)

        self.assertContains(response, f'You’re subscribed!')

    def test_webhook_subscription_created(self):
        fake_webhook_value = {
            'alert_name': 'subscription_created',
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'status': 'active',
            'passthrough': '1',
            'cancel_url': 'https://example.com',
            'update_url': 'https://example.com',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_update_plan(self):
        fake_webhook_value = {
            'alert_name': 'subscription_updated',
            'old_subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'subscription_plan_id': settings.PADDLE_STANDARD_ANNUAL,
            'status': 'active',
            'passthrough': '1',
            'cancel_url': 'https://example.com',
            'update_url': 'https://example.com',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_update_misc(self):
        fake_webhook_value = {
            'alert_name': 'subscription_updated',
            'old_subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'status': 'active',
            'passthrough': '1',
            'cancel_url': 'https://example.com',
            'update_url': 'https://example.com',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_cancelled(self):
        fake_webhook_value = {
            'alert_name': 'subscription_cancelled',
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'cancellation_effective_date': datetime.date.today(),
            'status': 'deleted',
            'passthrough': '1',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_payment_succeeded(self):
        fake_webhook_value = {
            'alert_name': 'subscription_payment_succeeded',
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'cancellation_effective_date': datetime.date.today(),
            'status': 'active',
            'passthrough': '1',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_payment_failed(self):
        fake_webhook_value = {
            'alert_name': 'subscription_payment_failed',
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'cancellation_effective_date': datetime.date.today(),
            'status': 'active',
            'passthrough': '1',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_subscription_payment_refunded(self):
        fake_webhook_value = {
            'alert_name': 'subscription_payment_refunded',
            'subscription_plan_id': settings.PADDLE_STANDARD_MONTHLY,
            'cancellation_effective_date': datetime.date.today(),
            'status': 'active',
            'passthrough': '1',
        }

        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data=fake_webhook_value)

        self.assertEqual(response.status_code, 200)

    def test_webhook_invalid_ip_address(self):
        with mock.patch('inventory.views.is_valid_ip_address', return_value=False):
            response = self.client.post(reverse('paddle-webhooks'))

        self.assertEqual(response.status_code, 403)

    def test_webhook_invalid_webhook(self):
        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=False):
                response = self.client.post(reverse('paddle-webhooks'))

        self.assertEqual(response.status_code, 400)

    def test_webhook_without_alert_name(self):
        with mock.patch('inventory.views.is_valid_ip_address', return_value=True):
            with mock.patch('inventory.views.is_valid_webhook', return_value=True):
                response = self.client.post(reverse('paddle-webhooks'), data={})

        self.assertEqual(response.status_code, 400)

    def test_subscription_update_success(self):
        plan = settings.PADDLE_STANDARD_MONTHLY
        fake_return_value = mock.Mock()
        fake_return_value.json = mock.Mock(return_value={'success': True})

        with mock.patch('inventory.views.requests.post', return_value=fake_return_value):
            response = self.client.post(reverse('subscription-update'), data={'plan': plan}, follow=True)

        self.assertContains(response, f'Your plan is now set to {paddle_plan_name(plan)}.')

    def test_subscription_update_with_error(self):
        plan = settings.PADDLE_STANDARD_MONTHLY
        error_message = 'You ain’t did it.'
        fake_return_value = mock.Mock()
        fake_return_value.json = mock.Mock(return_value={
            'success': False,
            'error': {'message': error_message},
        })

        with mock.patch('inventory.views.requests.post', return_value=fake_return_value):
            response = self.client.post(reverse('subscription-update'), data={'plan': plan}, follow=True)

        self.assertContains(response, f'There was a problem changing plans. “{error_message}” Please try again.')

    def test_subscription_update_with_invalid_plan(self):
        plan = '12345'
        fake_return_value = mock.Mock()
        fake_return_value.json = mock.Mock(return_value={'success': True})

        with mock.patch('inventory.views.requests.post', return_value=fake_return_value):
            response = self.client.post(reverse('subscription-update'), data={'plan': plan}, follow=True)

        self.assertContains(response, f'There was a problem changing plans. Please try again.')


@freeze_time(datetime.datetime.now())
@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SubscriptionBannerTests(TestCase):
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

    def test_subscription_banner_not_subscribed(self):
        self.user.profile.subscription_status = 'none'
        self.user.profile.save()

        response = self.client.get(reverse('settings'))
        self.assertContains(response, f'You have {settings.SUBSCRIPTION_TRIAL_DURATION} days left in your free trial.')

    def test_subscription_banner_cancelled(self):
        self.user.profile.subscription_status = 'deleted'
        self.user.profile.save()

        response = self.client.get(reverse('index'))

        self.assertContains(response, 'Your subscription has been cancelled.')

    def test_subscription_banner_past_due(self):
        self.user.profile.subscription_status = 'past_due'
        self.user.profile.save()

        response = self.client.get(reverse('index'))

        self.assertContains(response, 'Looks like there’s a problem with your subscription.')

    def test_subscription_banner_cancelling(self):
        self.user.profile.subscription_status = 'deleted'
        self.user.profile.paddle_cancellation_date = datetime.date.today() + datetime.timedelta(days=1)
        self.user.profile.save()

        response = self.client.get(reverse('index'))

        self.assertContains(response, 'Your subscription is scheduled to be canceled.')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class ProjectTests(TestCase):
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

    def test_empty_projects_page(self):
        response = self.client.get(reverse('projects'))
        project_add_url = reverse('project-add')
        self.assertContains(response, f'<a href="{project_add_url}">Add a project</a>', html=True)
        self.assertIsNotNone(response.context['projects'])

    def test_projects_page(self):
        baker.make(Project, owner=self.user)
        response = self.client.get(reverse('projects'))
        self.assertIsNotNone(response.context['projects'])

    def test_project_add_get(self):
        response = self.client.get(reverse('project-add'))
        self.assertEqual(response.status_code, 200)

    def test_project_add_post(self):
        response = self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
            'notes': 'A bunch of words.',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project added!', messages)

    def test_project_add_post_error_duplicate(self):
        self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        response = self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('You’ve already got a project with that name.', messages)

    def test_project_add_post_error_not_valid(self):
        response = self.client.post(reverse('project-add'), data={})
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Whoops! That didn’t work. Try again.', messages)

    def test_project_edit_get(self):
        self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        project = Project.objects.get(owner=self.user, name='A Project')
        response = self.client.get(reverse('project-edit', args=(project.id,)))
        self.assertEqual(response.status_code, 200)

    def test_project_edit_post(self):
        self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        project = Project.objects.get(owner=self.user, name='A Project')
        response = self.client.post(reverse('project-edit', args=(project.id,)), data={
            'name': 'A New Name',
            'status': 'current',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project updated!', messages)

    def test_project_edit_post_archived_with_rolls(self):
        self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        project = Project.objects.get(owner=self.user, name='A Project')
        baker.make(Roll, owner=self.user, project=project)
        response = self.client.post(reverse('project-edit', args=(project.id,)), data={
            'name': 'A New Name',
            'status': 'archived',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project archived and 1 roll now available for other projects.', messages)

    def test_project_edit_post_archived_without_rolls(self):
        self.client.post(reverse('project-add'), data={
            'name': 'A Project',
            'status': 'current',
        })
        project = Project.objects.get(owner=self.user, name='A Project')
        response = self.client.post(reverse('project-edit', args=(project.id,)), data={
            'name': 'A New Name',
            'status': 'archived',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project archived!', messages)

    def test_project_delete(self):
        project = baker.make(Project, owner=self.user)
        response = self.client.post(reverse('project-delete', args=(project.id,)))
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project deleted.', messages)

    def test_project_delete_with_rolls(self):
        project = baker.make(Project, owner=self.user)
        baker.make(Roll, owner=self.user, project=project)
        baker.make(Roll, owner=self.user, project=project)
        response = self.client.post(reverse('project-delete', args=(project.id,)))
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Project deleted and 2 rolls now available for other projects.', messages)

    def test_project_detail(self):
        film = baker.make(Film, slug='slug')
        project = baker.make(Project, owner=self.user)
        camera1 = baker.make(Camera, owner=self.user, multiple_backs=True)
        camera2 = baker.make(Camera, owner=self.user)
        camera3 = baker.make(Camera, owner=self.user)
        camera4 = baker.make(Camera, owner=self.user)
        baker.make(Roll, film=film, status=status_number('loaded'), camera=camera2, owner=self.user, project=project)
        baker.make(Roll, film=film, status=status_number('storage'), owner=self.user, project=project)
        baker.make(Roll, film=film, status=status_number('loaded'), camera=camera4, owner=self.user)
        project.cameras.add(camera1)
        project.cameras.add(camera2)
        project.cameras.add(camera3)
        project.cameras.add(camera4)
        baker.make(CameraBack, camera=camera1)

        response = self.client.get(reverse('project-detail', args=(project.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '(filtered)')

    def test_project_detail_htmx(self):
        project = baker.make(Project, owner=self.user)
        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.get(reverse('project-detail', args=(project.id,)), **headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/project-camera-logbook-wrapper.html')

    def test_project_rolls_add(self):
        project = baker.make(Project, owner=self.user)
        film = baker.make(Film)
        baker.make(Roll, film=film, owner=self.user)
        response = self.client.post(reverse('project-rolls-add', args=(project.id,)), data={
            'quantity': 1,
            'film': film.id
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'1 roll of {film} added!', messages)

    def test_project_rolls_add_error(self):
        project = baker.make(Project, owner=self.user)
        film = baker.make(Film)
        response = self.client.post(reverse('project-rolls-add', args=(project.id,)), data={
            'quantity': 1,
            'film': film.id
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'You don’t have that many rolls of {film} available.', messages)

    def test_project_rolls_remove(self):
        project = baker.make(Project, owner=self.user)
        film = baker.make(Film)
        baker.make(Roll, film=film, owner=self.user, project=project)

        response = self.client.post(reverse('project-rolls-remove', args=(project.id,)), data={
            'film': film.id
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'Removed 1 roll of {film} from this project!', messages)

    def test_project_rolls_remove_error(self):
        project = baker.make(Project, owner=self.user)
        film = baker.make(Film)

        response = self.client.post(reverse('project-rolls-remove', args=(project.id,)), data={
            'film': film.id
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'You don’t have any rolls of {film} to remove.', messages)

    def test_project_camera_update_add(self):
        project = baker.make(Project, owner=self.user)
        camera = baker.make(Camera, owner=self.user)
        response = self.client.post(reverse('project-camera-update', args=(project.id,)), data={
            'camera': camera.id,
            'action': 'add',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'{camera} added to this project!', messages)

    def test_project_camera_update_remove(self):
        project = baker.make(Project, owner=self.user)
        camera = baker.make(Camera, owner=self.user)
        project.cameras.add(camera)
        response = self.client.post(reverse('project-camera-update', args=(project.id,)), data={
            'camera': camera.id,
            'action': 'remove',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'{camera} removed from this project!', messages)

    def test_project_camera_update_error(self):
        project = baker.make(Project, owner=self.user)
        camera = baker.make(Camera, owner=self.user)
        response = self.client.post(reverse('project-camera-update', args=(project.id,)), data={
            'camera': camera.id,
            'action': 'not-an-action',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Something is amiss.', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class CameraViewTests(TestCase):
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

    def test_cameras_page(self):
        response = self.client.get(reverse('cameras'))
        self.assertEqual(response.status_code, 200)

    def test_camera_add_get(self):
        response = self.client.get(reverse('camera-add'))
        self.assertEqual(response.status_code, 200)

    def test_camera_add_post(self):
        response = self.client.post(reverse('camera-add'), data={
            'name': 'A 35mm Camera',
            'format': '135',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'Camera added!', messages)

    def test_camera_add_post_add_another(self):
        response = self.client.post(reverse('camera-add'), data={
            'name': 'A 35mm Camera',
            'format': '135',
            'another': True,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('camera-add'))
        self.assertIn(f'Camera added!', messages)

    def test_camera_add_post_error(self):
        # Not including required fields.
        response = self.client.post(reverse('camera-add'), data={})
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Something is amiss. Please try again.', messages)

    def test_camera_edit_get(self):
        camera = baker.make(Camera, owner=self.user)
        response = self.client.get(reverse('camera-edit', args=(camera.id,)))
        self.assertEqual(response.status_code, 200)

    def test_camera_edit_post(self):
        camera = baker.make(Camera, owner=self.user)
        response = self.client.post(reverse('camera-edit', args=(camera.id,)), data={
            'name': 'A new name',
            'format': '135',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('camera-detail', args=(camera.id,)))
        self.assertIn('Camera updated!', messages)

    def test_camera_edit_post_unavailable(self):
        # Get that 100% test coverage for the view.
        camera = baker.make(Camera, owner=self.user)
        response = self.client.post(reverse('camera-edit', args=(camera.id,)), data={
            'name': 'A new name',
            'format': '135',
            'unavailable': True,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('camera-detail', args=(camera.id,)))
        self.assertIn('Camera updated!', messages)

    def test_camera_edit_post_error(self):
        camera = baker.make(Camera, owner=self.user)
        # Not including required fields.
        response = self.client.post(reverse('camera-edit', args=(camera.id,)), data={})
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('camera-detail', args=(camera.id,)))
        self.assertIn('Something is amiss. Please try again.', messages)

    def test_camera_detail(self):
        camera = baker.make(Camera, owner=self.user)
        response = self.client.get(
            reverse('camera-detail', args=(camera.id,))
        )
        self.assertEqual(response.status_code, 200)

    def test_camera_back_detail(self):
        camera_back = baker.make(CameraBack, camera=baker.make(Camera, owner=self.user))
        response = self.client.get(
            reverse('camera-back-detail', args=(camera_back.camera.id, camera_back.id))
        )
        self.assertEqual(response.status_code, 200)

    def test_camera_or_back_detail_htmx(self):
        camera = baker.make(Camera, owner=self.user)
        headers1 = {'HTTP_HX-Request': 'true', 'HTTP_HX-Trigger': 'monkey'}
        response1 = self.client.get(reverse('camera-detail', args=(camera.id,)), **headers1)

        self.assertEqual(response1.status_code, 200)
        self.assertTemplateUsed(response1, 'components/logbook-table.html')

        camera2 = baker.make(Camera, owner=self.user, multiple_backs=True)
        headers2 = {'HTTP_HX-Request': 'true', 'HTTP_HX-Trigger': 'section'}
        response2 = self.client.get(reverse('camera-detail', args=(camera2.id,)), **headers2)

        self.assertEqual(response2.status_code, 200)
        self.assertTemplateUsed(response2, 'components/section.html')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class RollViewTests(TestCase):
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

    def test_roll_edit_get(self):
        roll = baker.make(Roll, owner=self.user)
        response = self.client.get(reverse('roll-edit', args=(roll.id,)))
        self.assertEqual(response.status_code, 200)

    def test_roll_edit_post(self):
        roll = baker.make(Roll, owner=self.user)
        roll.film = baker.make(Film, slug='slug', iso=100)
        roll.camera = baker.make(Camera, owner=self.user)
        roll.camera_back = baker.make(CameraBack, camera=roll.camera)
        roll.save()
        response = self.client.post(reverse('roll-edit', args=(roll.id,)), data={
            'lens': '50mm f/1.4',
            'push_pull': '+2',
            'status': status_number('storage'),
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('roll-detail', args=(roll.id,)))
        self.assertIn('Changes saved!', messages)


@override_flag('frames', active=True)
@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class FrameViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        cls.roll = baker.make(Roll, owner=cls.user)
        baker.make(
            Frame,
            roll=cls.roll,
            date=cls.today,
            number=1,
        )

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_frame_create(self):
        response = self.client.post(reverse('roll-frame-add', args=(self.roll.id,)), data={
            'number': '2',
            'date': self.today,
            'aperture': '1',
            'shutter_speed': '1/500',
            'notes': 'asdf',
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Frame saved!', messages)

    def test_frame_create_multiple(self):
        response = self.client.post(reverse('roll-frame-add', args=(self.roll.id,)), data={
            'number': '2',
            'date': self.today,
            'ending_number': '4',
            'aperture': '1',
            'shutter_speed': '1/500',
            'notes': 'asdf',
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('3 frames saved!', messages)

    def test_frame_create_and_add_another(self):
        response = self.client.post(reverse('roll-frame-add', args=(self.roll.id,)), data={
            'number': '2',
            'date': self.today,
            'aperture': '1',
            'shutter_speed': '1/500',
            'notes': 'asdf',
            'another': True,
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url=reverse('roll-frame-add', args=(self.roll.id,)))
        self.assertIn('Frame saved!', messages)

    def test_frame_create_and_add_another_with_inputs(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        frame = baker.make(Frame, roll=self.roll, date=yesterday, aperture='abcd', shutter_speed='efgh')
        response = self.client.get(reverse('roll-frame-add', args=(self.roll.id,)) + '?another')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['date'].value(), yesterday)
        self.assertTrue(response.context['show_input']['aperture'])
        self.assertTrue(response.context['show_input']['shutter_speed'])

    def test_frame_create_and_add_another_with_presets(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        frame = baker.make(Frame, roll=self.roll, date=yesterday, aperture='2', shutter_speed='1/500')
        response = self.client.get(reverse('roll-frame-add', args=(self.roll.id,)) + '?another')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['date'].value(), yesterday)
        self.assertFalse(response.context['show_input']['aperture'])
        self.assertFalse(response.context['show_input']['shutter_speed'])

    def test_frame_create_error(self):
        response = self.client.post(reverse('roll-frame-add', args=(self.roll.id,)), data={
            'number': '1',
            'date': self.today,
            'aperture': '1',
            'shutter_speed': '1/500',
            'notes': 'asdf',
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'This roll already has frame #1.', messages)

    def test_frame_create_first(self):
        # First frame of a roll.

        roll = baker.make(Roll, owner=self.user)
        response = self.client.get(reverse('roll-frame-add', args=(roll.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['number'], 1)

    def test_frame_create_presets(self):
        response = self.client.post(reverse('roll-frame-add', args=(self.roll.id,)), data={
            'number': '2',
            'date': self.today,
            'aperture_preset': '1.4',
            'shutter_speed_preset': '1/500',
            'notes': 'asdf',
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('Frame saved!', messages)

    def test_frame_read(self):
        response = self.client.get(reverse('roll-frame-detail', args=(self.roll.id, 1)))

        self.assertEqual(response.status_code, 200)

    def test_frame_update_page_with_presets(self):
        frame = baker.make(Frame, roll=self.roll, number='2', aperture='1.4', shutter_speed='1/500')
        response = self.client.get(reverse('roll-frame-edit', args=(self.roll.id, 2)))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['show_input']['aperture'])
        self.assertFalse(response.context['show_input']['shutter_speed'])

    def test_frame_update_page_with_inputs(self):
        frame = baker.make(Frame, roll=self.roll, number='2', aperture='abcd', shutter_speed='efgh')
        response = self.client.get(reverse('roll-frame-edit', args=(self.roll.id, 2)))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_input']['aperture'])
        self.assertTrue(response.context['show_input']['shutter_speed'])

    def test_frame_update(self):
        roll = baker.make(Roll, owner=self.user)
        frame_number = 2
        frame = baker.make(Frame, roll=roll, number=frame_number, date=self.today, aperture='1', shutter_speed='1/60')

        response = self.client.post(reverse('roll-frame-edit', args=(roll.id, frame_number)), data={
            'number': '2',
            'date': self.today,
            'aperture': '1.4',
            'shutter_speed': '1/500',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(frame.aperture, '1.4')
        self.assertTrue(frame.shutter_speed, '1/60')

    def test_frame_update_with_presets(self):
        roll = baker.make(Roll, owner=self.user)
        frame_number = 2
        frame = baker.make(Frame, roll=roll, number=frame_number, date=self.today, aperture='1', shutter_speed='1/60')

        response = self.client.post(reverse('roll-frame-edit', args=(roll.id, frame_number)), data={
            'number': '2',
            'date': self.today,
            'aperture_preset': '1.4',
            'shutter_speed_preset': '1/500',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(frame.aperture, '1.4')
        self.assertTrue(frame.shutter_speed, '1/500')

    def test_frame_edit_error(self):
        roll = baker.make(Roll, owner=self.user)
        baker.make(Frame, roll=roll, number=1, date=self.today)
        baker.make(Frame, roll=roll, number=2, date=self.today)

        response = self.client.post(reverse('roll-frame-edit', args=(roll.id, 2)), data={
            'number': '1',
            'date': self.today,
        })

        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'This roll already has frame #1.', messages)

    def test_frame_delete(self):
        roll = baker.make(Roll, owner=self.user)
        frame = baker.make(Frame, roll=roll, date=self.today, number=1)
        response = self.client.post(reverse('roll-frame-delete', args=(roll.id, frame.number)))
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn(f'{frame} successfully deleted.', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class StockViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.today = datetime.date.today()
        cls.public_stock = baker.make(
            Stock,
            name='Portra 400',
            slug='portra-400',
            manufacturer=baker.make(Manufacturer, name='Kodak', slug='kodak')
        )
        cls.personal_stock = baker.make(
            Stock,
            name='Dracula',
            personal=True,
            added_by=cls.user,
            manufacturer=baker.make(Manufacturer, name='FPP', slug='fpp')
        )
        cls.stocks_url = reverse('stocks')

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )
        # Reduce the log level to avoid errors like "not found."
        logger = logging.getLogger('django.request')
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

    def tearDown(self):
        # Reset the log level back to normal.
        logger = logging.getLogger('django.request')
        logger.setLevel(self.previous_level)

    def test_stocks_page(self):
        response = self.client.get(reverse('stocks'))
        self.assertContains(response, f'{self.public_stock.manufacturer.name} {self.public_stock.name}')
        self.assertContains(response, f'{self.personal_stock.manufacturer.name} {self.personal_stock.name}')
        self.assertIsNotNone(response.context['stocks'])

    def test_stocks_page_with_filtering_type(self):
        response = self.client.get(reverse('stocks') + '?type=c41')
        self.assertContains(response, f'{self.public_stock.manufacturer.name} {self.public_stock.name}')
        self.assertContains(response, f'{self.personal_stock.manufacturer.name} {self.personal_stock.name}')
        self.assertIsNotNone(response.context['stocks'])
        self.assertContains(response, '<span>C41 Color</span>', html=True)

    def test_stocks_page_with_manufacturer_redirect(self):
        response = self.client.get(reverse('stocks') + '?manufacturer=kodak&type=c41')
        self.assertEqual(response.status_code, 302)

    def test_stocks_page_with_unavailable_type(self):
        response = self.client.get(
            reverse('stocks-manufacturer', args=(self.public_stock.manufacturer.slug,)) + '?type=bw'
        )
        self.assertEqual(response.status_code, 302)

    def test_stocks_page_logged_out(self):
        self.client.logout()
        response = self.client.get(reverse('stocks'))
        self.assertContains(response, f'{self.public_stock.manufacturer.name} {self.public_stock.name}')
        self.assertNotContains(response, f'{self.personal_stock.manufacturer.name} {self.personal_stock.name}')
        self.assertIsNotNone(response.context['stocks'])

    def test_stocks_manufacturer_page(self):
        response = self.client.get(reverse('stocks-manufacturer', args=(self.public_stock.manufacturer.slug,)))
        self.assertContains(response, f'{self.public_stock.manufacturer.name} {self.public_stock.name}')
        self.assertIsNotNone(response.context['stocks'])

    def test_stock_page(self):
        response = self.client.get(reverse('stock', args=(self.public_stock.manufacturer.slug, self.public_stock.slug)))
        self.assertContains(response, f'{self.public_stock.name}')
        self.assertContains(response, 'Your inventory of this stock')
        self.assertIsNotNone(response.context['stock'])

    def test_stock_page_logged_out(self):
        self.client.logout()
        response = self.client.get(reverse('stock', args=(self.public_stock.manufacturer.slug, self.public_stock.slug)))
        self.assertContains(response, f'{self.public_stock.name}')
        self.assertNotContains(response, 'Your inventory of this stock')
        self.assertIsNotNone(response.context['stock'])

    # HTMX / Ajax
    def test_stocks_htmx_with_type(self):
        response = stocks(htmx_request(get_url=f'{self.stocks_url}?manufacturer=all&type=c41', user=self.user))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset filters')

    def test_stocks_htmx_with_manufacturer(self):
        response = stocks(htmx_request(get_url=f'{self.stocks_url}?manufacturer=kodak&type=c41', user=self.user))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset filters')

    def test_stocks_htmx_logged_out(self):
        # Not passing `user` to `htmx_request()`.
        response = stocks(htmx_request(get_url=f'{self.stocks_url}?manufacturer=kodak&type=c41'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset filters')

    def test_personal_stock_logged_in(self):
        response = self.client.get(
            reverse('stock', args=(self.personal_stock.manufacturer.slug, self.personal_stock.slug))
        )
        self.assertEqual(response.status_code, 200)

    def test_personal_stock_404_logged_out(self):
        self.client.logout()
        response = self.client.get(
            reverse('stock', args=(self.personal_stock.manufacturer.slug, self.personal_stock.slug))
        )
        self.assertEqual(response.status_code, 404)

    def test_personal_stock_404_logged_in(self):
        stock = baker.make(Stock, personal=True, added_by=baker.make(User))
        response = self.client.get(reverse('stock', args=(stock.manufacturer.slug, stock.slug)))
        self.assertEqual(response.status_code, 404)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class StockAddTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'test'
        cls.password = 'secret'
        cls.user = User.objects.create_user(
            username=cls.username,
            password=cls.password,
        )
        cls.manufacturer = baker.make(Manufacturer, name='Kodak', slug='kodak')

    def setUp(self):
        self.client.login(
            username=self.username,
            password=self.password,
        )

    def test_stock_add_page(self):
        response = self.client.get(reverse('stock-add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Film Stock')

    def test_stock_add_page_with_destination(self):
        response = self.client.get(reverse('stock-add') + f'?destination=add-logbook')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Film Stock')

    def test_adding_new_stock(self):
        response = self.client.post(reverse('stock-add'), data={
            'manufacturer': self.manufacturer.id,
            'name': 'Ektar 100',
            'formats': [135],
            'type': 'c41',
            'iso': 100,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('New film stock “Kodak Ektar 100” (in 35mm) added!', messages)

    def test_adding_new_stock_and_new_manufacturer(self):
        response = self.client.post(reverse('stock-add'), data={
            'new_manufacturer': 'Fujifilm',
            'name': 'Provia 100',
            'formats': [135, 120],
            'type': 'e6',
            'iso': 100,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('New film stock “Fujifilm Provia 100” (in 35mm, 120) added!', messages)

    def test_adding_new_stock_and_new_manufacturer_error(self):
        response = self.client.post(reverse('stock-add'), data={
            'new_manufacturer': self.manufacturer.name,
            'name': 'Ektar 100',
            'formats': [135],
            'type': 'c41',
            'iso': 100,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 200)
        self.assertIn('There’s already a manufacturer with that name.', messages)

    def test_adding_new_stock_and_another(self):
        response = self.client.post(reverse('stock-add'), data={
            'manufacturer': self.manufacturer.id,
            'name': 'Gold 200',
            'formats': [135],
            'type': 'c41',
            'iso': 200,
            'another': True,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('New film stock “Kodak Gold 200” (in 35mm) added!', messages)

    def test_adding_new_stock_from_inventory(self):
        response = self.client.post(reverse('stock-add'), data={
            'manufacturer': self.manufacturer.id,
            'name': 'UltraMax 400',
            'formats': [135],
            'type': 'c41',
            'iso': 400,
            'destination': 'add-storage',
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('New film stock “Kodak UltraMax 400” (in 35mm) added!', messages)

    def test_adding_new_stock_from_inventory_and_another(self):
        response = self.client.post(reverse('stock-add'), data={
            'manufacturer': self.manufacturer.id,
            'name': 'Tri-X 400',
            'formats': [135, 120],
            'type': 'c41',
            'iso': 400,
            'destination': 'add-storage',
            'another': True,
        })
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertIn('New film stock “Kodak Tri-X 400” (in 35mm, 120) added!', messages)


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SubscriptionRequirementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active_user = User.objects.create_user('active')
        trial_duration = datetime.timedelta(days=int(settings.SUBSCRIPTION_TRIAL_DURATION))
        with freeze_time(datetime.date.today() - trial_duration):
            cls.inactive_user = User.objects.create_user('inactive')

        film = baker.make(Film, stock=baker.make(Stock))
        cls.roll1 = baker.make(Roll, owner=cls.active_user, film=film)
        cls.roll2 = baker.make(Roll, owner=cls.inactive_user, film=film)

    def test_account_inactive_page(self):
        self.client.force_login(self.inactive_user)
        response = self.client.get(reverse('account-inactive'))
        self.assertEqual(response.status_code, 200)

    def test_account_inactive_page_redirect(self):
        self.client.force_login(self.active_user)
        response = self.client.get(reverse('account-inactive'))
        self.assertEqual(response.status_code, 302)

    def test_hidden_edit_controls(self):
        self.client.force_login(self.inactive_user)
        response = self.client.get(reverse('roll-detail', args=(self.roll2.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="action"')

    def test_visible_edit_controls(self):
        self.client.force_login(self.active_user)
        response = self.client.get(reverse('roll-detail', args=(self.roll1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="action"')


@override_settings(STATICFILES_STORAGE=staticfiles_storage)
class SidebarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='test',
            password='secret',
        )

    def setUp(self):
        # Reduce the log level to avoid errors like "not found."
        logger = logging.getLogger('django.request')
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client.force_login(user=self.user)

    def tearDown(self):
        # Reset the log level back to normal.
        logger = logging.getLogger('django.request')
        logger.setLevel(self.previous_level)

    def test_sidebar_status_ajax(self):
        headers = {'HTTP_X-Requested-With': 'XMLHttpRequest'}
        response = self.client.get(reverse('session-sidebar-status'), **headers)

        self.assertEqual(response.status_code, 200)

    def test_sidebar_status_without_ajax(self):
        response = self.client.get(reverse('session-sidebar-status'))

        self.assertEqual(response.status_code, 403)

    def test_sidebar_htmx(self):
        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.get(reverse('session-sidebar'), **headers)

        self.assertEqual(response.status_code, 200)

    def test_sidebar_without_htmx(self):
        response = self.client.get(reverse('session-sidebar'))

        self.assertEqual(response.status_code, 403)
