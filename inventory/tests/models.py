import datetime
from django.test import TestCase
from model_bakery import baker
from inventory.models import Roll, Camera, CameraBack
from inventory.utils import status_number


class RollTests(TestCase):
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

        roll.started_on = datetime.date.today()
        roll.camera = camera
        # Save to create a code for the roll.
        roll.save()

        self.assertEqual(camera.status, 'loaded')
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
