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
)
from inventory.utils import status_number


class ProfileTests(TestCase):
    def test_model_str(self):
        username = 'testy'
        user = baker.make(User, username=username)

        self.assertEqual(str(user.profile), f'Settings for {username}')

    def test_has_active_subscription(self):
        user = baker.make(User)

        self.assertFalse(user.profile.has_active_subscription)

    def test_creating_profile_for_legacy_user(self):
        # This is for users that were created before automatic profiles were in place.

        # Create a user with `bulk_create` so that `post_save` doesn’t run and
        # create a Profile.
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
        roll.started_on = datetime.date.today()
        roll.save()
        self.assertEqual(roll.code, '35-c41-1')
        self.assertEqual(roll.status, status_number('loaded'))

    def test_rolls_get_correct_code_sequence(self):
        camera1 = baker.make(Camera)
        camera2 = baker.make(Camera)
        camera3 = baker.make(Camera)
        camera4 = baker.make(Camera)
        camera5 = baker.make(Camera)
        camera6 = baker.make(Camera)

        roll1 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            camera=camera1,
            started_on=datetime.date.today()
        )
        roll2 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            camera=camera2,
            started_on=datetime.date.today()
        )
        roll3 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            camera=camera3,
            started_on=datetime.date.today()
        )
        roll4 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            camera=camera4,
            started_on=datetime.date.today()
        )
        roll5 = baker.make(
            Roll,
            owner__id=1,
            film__type='bw',
            camera=camera5,
            started_on=datetime.date.today()
        )
        # A different user.
        roll6 = baker.make(
            Roll,
            owner__id=2,
            film__type='bw',
            camera=camera6,
            started_on=datetime.date.today()
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
        roll = baker.make(Roll)
        camera = baker.make(Camera)
        camera_back = baker.make(CameraBack)

        roll.started_on = datetime.date.today()
        roll.camera = camera
        roll.camera_back = camera_back
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
        roll = baker.make(Roll)
        camera = baker.make(Camera)

        roll.started_on = datetime.date.today()
        roll.camera = camera
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
        roll = baker.make(Roll)
        camera = baker.make(Camera)

        self.assertIsNone(roll.ended_on)

        roll.camera = camera
        roll.started_on = datetime.date.today()
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
        roll = baker.make(Roll)
        camera = baker.make(Camera)
        camera_back = baker.make(CameraBack)

        roll.camera = camera
        roll.camera_back = camera_back
        roll.started_on = datetime.date.today()
        roll.save()

        self.assertEqual(camera_back.status, 'loaded')

        roll.status = status_number('shot')
        roll.save()

        self.assertEqual(camera_back.status, 'empty')


class CameraTests(TestCase):
    def test_model_str(self):
        name = 'Cameraface'
        camera = baker.make(Camera, name=name)

        self.assertEqual(str(camera), name)

    def test_get_absolute_url(self):
        camera = baker.make(Camera, id=1)

        self.assertEqual(camera.get_absolute_url(), '/camera/1/')


class CameraBackTests(TestCase):
    def test_model_str(self):
        camera_name = 'Cameraface'
        back_name = 'A'
        camera = baker.make(Camera, name=camera_name)
        back = baker.make(CameraBack, camera=camera, name=back_name)

        self.assertEqual(str(back), f'{camera_name}, Back “{back_name}”')


class ProjectTests(TestCase):
    def test_model_str(self):
        name = 'Superduper'
        project = baker.make(Project, name=name)

        self.assertEqual(str(project), name)

    def test_get_absolute_url(self):
        project = baker.make(Project, id=1)

        self.assertEqual(project.get_absolute_url(), '/project/1/')

    def test_get_rolls_remaining(self):
        project = baker.make(Project)
        roll = baker.make(Roll, project=project)

        self.assertEqual(project.get_rolls_remaining(), 1)

        roll.status = status_number('shot')
        roll.save()

        self.assertEqual(project.get_rolls_remaining(), 0)
