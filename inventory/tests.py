import datetime
from django.test import TestCase
from model_bakery import baker
from .models import Roll, Camera
from .utils import status_number


class RollTestCase(TestCase):
    def test_loaded_rolls_get_code_and_status(self):
        roll = baker.make(Roll)
        roll.started_on = datetime.date.today()
        roll.save()
        self.assertEqual(roll.code, '35-c41-1')
        self.assertEqual(roll.status, status_number('loaded'))

    def test_rolls_get_correct_code_sequence(self):
        roll1 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            started_on=datetime.date.today()
        )
        roll2 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            started_on=datetime.date.today()
        )
        roll3 = baker.make(
            Roll,
            owner__id=1,
            film__type='e6',
            started_on=datetime.date.today()
        )
        roll4 = baker.make(
            Roll,
            owner__id=1,
            film__type='c41',
            started_on=datetime.date.today()
        )
        roll5 = baker.make(
            Roll,
            owner__id=1,
            film__type='bw',
            started_on=datetime.date.today()
        )
        roll6 = baker.make(
            Roll,
            owner__id=2,
            film__type='bw',
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

    def test_rolls_change_from_loaded_to_storage(self):
        roll = baker.make(Roll)
        camera = baker.make(Camera)

        roll.started_on = datetime.date.today()
        roll.camera = camera
        camera.status = 'loaded'
        # Save to create a code for the roll.
        roll.save()

        self.assertEqual(camera.status, 'loaded')
        self.assertIsNotNone(roll.camera)

        roll.status = status_number('storage')
        # Save again to reset code and unload camera.
        roll.save()

        self.assertEqual(roll.code, '')
        self.assertIsNone(roll.camera)
        self.assertEqual(camera.status, 'empty')
