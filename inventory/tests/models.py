import datetime
from django.test import TestCase
from model_bakery import baker
from django.contrib.auth.models import User
from inventory.models import (
    Film,
    Roll,
    Camera,
    CameraBack,
    Profile,
    Project,
    Journal,
)
from inventory.utils import status_number


class ProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'testy'
        cls.user = baker.make(User, username=cls.username)

    def test_model_str(self):
        self.assertEqual(str(self.user.profile), f'Settings for {self.username}')

    def test_has_active_subscription(self):
        self.assertFalse(self.user.profile.has_active_subscription)

    def test_creating_profile_for_legacy_user(self):
        # This is for users that were created before automatic profiles were in place.

        # Create a user with `bulk_create` so that `post_save` doesn’t run and create a Profile.
        User.objects.bulk_create([
            User(id=1, username='test', password='testtest'),
        ])

        user = User.objects.get(id=1)

        with self.assertRaises(User.profile.RelatedObjectDoesNotExist):
            profile = user.profile

        user.save()
        self.assertIsInstance(user.profile, Profile)


class FilmTests(TestCase):
    def test_get_absolute_url(self):
        slug = 'filmy'
        film = baker.make(Film, slug=slug)

        self.assertEqual(film.get_absolute_url(), f'/film/{slug}/')


class RollTests(TestCase):
    def test_model_str(self):
        manufacturer = 'Awesome'
        film = 'Filmy'

        roll = baker.make(
            Roll,
            film__manufacturer__name=manufacturer,
            film__name=film,
        )

        self.assertEqual(
            str(roll),
            f'{manufacturer} {film} in 35mm added on {datetime.datetime.utcnow().date()}'
        )

        roll.camera = baker.make(Camera)
        roll.started_on = datetime.datetime.utcnow().date()
        roll.save()

        self.assertEqual(str(roll), f'35-c41-1 / {roll.started_on.year}')

    def test_effective_iso(self):
        film = baker.make(Film, iso=400)
        roll1 = baker.make(Roll, film=film)
        roll2 = baker.make(Roll, film=film, push_pull='+2')

        self.assertEqual(roll1.effective_iso, 400)
        self.assertEqual(roll2.effective_iso, 1600)

    def test_loaded_rolls_get_code_and_status(self):
        roll = baker.make(Roll)
        camera = baker.make(Camera)

        roll.camera = camera
        roll.started_on = datetime.datetime.utcnow().date()
        roll.save()
        self.assertEqual(roll.code, '35-c41-1')
        self.assertEqual(roll.status, status_number('loaded'))

    def test_rolls_get_correct_code_sequence(self):
        today = datetime.datetime.utcnow().date()
        roll1 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            camera=baker.make(Camera),
            started_on=today
        )
        roll2 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            camera=baker.make(Camera),
            started_on=today
        )
        roll3 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            camera=baker.make(Camera),
            started_on=today
        )
        roll4 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            camera=baker.make(Camera),
            started_on=today
        )
        roll5 = baker.make(
            Roll,
            owner__id=1,
            film__type='bw',
            camera=baker.make(Camera),
            started_on=today
        )
        # A different user.
        roll6 = baker.make(
            Roll,
            owner__id=2,
            film__type='bw',
            camera=baker.make(Camera),
            started_on=today
        )

        roll1.save()
        roll2.save()
        roll3.save()
        roll4.save()
        roll5.save()
        roll6.save()

        self.assertEqual(roll1.code, '35-e6-1')
        self.assertEqual(roll2.code, '35-c41-1')
        self.assertEqual(roll3.code, '35-e6-2')
        self.assertEqual(roll4.code, '35-c41-2')
        self.assertEqual(roll5.code, '35-bw-1')
        self.assertEqual(roll6.code, '35-bw-1')

    def test_roll_change_from_loaded_to_storage(self):
        camera = baker.make(Camera)
        camera_back = baker.make(CameraBack)
        roll = baker.make(Roll, camera=camera, camera_back=camera_back)

        roll.started_on = datetime.datetime.utcnow().date()
        # Save to create a code for the roll.
        roll.save()

        self.assertEqual(camera.status, 'loaded')
        self.assertEqual(camera_back.status, 'loaded')
        self.assertIsNotNone(roll.camera)

        roll.status = status_number('storage')
        # Save again to reset code and unload camera.
        roll.save()

        self.assertEqual(roll.code, '')
        self.assertEqual(roll.push_pull, '')
        self.assertIsNone(roll.camera)
        self.assertIsNone(roll.started_on)
        self.assertIsNone(roll.ended_on)
        self.assertEqual(camera.status, 'empty')
        self.assertEqual(camera_back.status, 'empty')

    def test_roll_change_from_loaded_to_shot(self):
        camera = baker.make(Camera)
        roll = baker.make(Roll, camera=camera)

        roll.started_on = datetime.datetime.utcnow().date()
        # Save to create a code for the roll and load camera.
        roll.save()

        self.assertEqual(camera.status, 'loaded')
        roll.status = status_number('shot')
        # Save again to unload camera.
        roll.save()

        self.assertEqual(roll.code, '35-c41-1')
        self.assertEqual(roll.ended_on, roll.started_on)
        self.assertEqual(camera.status, 'empty')

    def test_roll_change_from_shot_to_loaded(self):
        camera = baker.make(Camera)
        roll = baker.make(Roll, camera=camera)

        self.assertIsNone(roll.ended_on)

        roll.started_on = datetime.datetime.utcnow().date()
        roll.status = status_number('shot')
        # Save to set ended_on and unload camera.
        roll.save()

        self.assertIsNotNone(roll.ended_on)
        self.assertEqual(camera.status, 'empty')

        roll.status = status_number('loaded')
        # Save again to re-load camera and remove ended_on.
        roll.save()

        self.assertIsNone(roll.ended_on)
        self.assertEqual(camera.status, 'loaded')

    def test_loading_and_unloading_camera_back(self):
        camera_back = baker.make(CameraBack)
        roll = baker.make(
            Roll,
            camera=baker.make(Camera),
            started_on=datetime.datetime.utcnow().date(),
            camera_back=camera_back,
        )

        self.assertEqual(camera_back.status, 'loaded')

        roll.status = status_number('shot')
        roll.save()

        self.assertEqual(camera_back.status, 'empty')


class CameraTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.id = 1
        cls.name = 'Cameraface'
        cls.camera = baker.make(Camera, id=cls.id, name=cls.name)

    def test_model_str(self):
        self.assertEqual(str(self.camera), self.name)

    def test_get_absolute_url(self):
        self.assertEqual(self.camera.get_absolute_url(), f'/camera/{self.id}/')


class CameraBackTests(TestCase):
    def test_model_str(self):
        camera_name = 'Cameraface'
        back_name = 'A'
        camera = baker.make(Camera, name=camera_name)
        back = baker.make(CameraBack, camera=camera, name=back_name)

        self.assertEqual(str(back), f'{camera_name}, Back “{back_name}”')


class ProjectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.id = 1
        cls.name = 'Superduper'
        cls.project = baker.make(Project, id=cls.id, name=cls.name)

    def test_model_str(self):
        self.assertEqual(str(self.project), self.name)

    def test_get_absolute_url(self):
        self.assertEqual(self.project.get_absolute_url(), f'/project/{self.id}/')

    def test_get_rolls_remaining(self):
        roll = baker.make(Roll, project=self.project)

        self.assertEqual(self.project.get_rolls_remaining(), 1)

        roll.status = status_number('shot')
        roll.save()

        self.assertEqual(self.project.get_rolls_remaining(), 0)


class JournalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = datetime.datetime.utcnow().date()
        cls.yesterday = cls.today - datetime.timedelta(days=1)

    def test_model_str(self):
        roll = baker.make(Roll, started_on=self.today, camera=baker.make(Camera))
        journal = baker.make(Journal, roll=roll, date=self.today)

        self.assertEqual(str(journal), f'Journal entry for 35-c41-1 on {self.today}')

    def test_starting_frame(self):
        roll = baker.make(Roll, started_on=self.yesterday, camera=baker.make(Camera))
        journal1 = baker.make(Journal, roll=roll, date=self.yesterday, frame=3)
        journal2 = baker.make(Journal, roll=roll, date=self.today)

        self.assertEqual(journal1.starting_frame, 1)
        self.assertEqual(journal2.starting_frame, 4)
