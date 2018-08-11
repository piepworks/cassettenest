from django.test import TestCase
from model_mommy import mommy
from .models import Roll
from .utils import *
import datetime


class RollTestCase(TestCase):
    def test_loaded_rolls_get_code_and_status(self):
        roll = mommy.make(Roll)
        roll.started_on = datetime.date.today()
        roll.save()
        self.assertEqual(roll.code, '35-c41-1')
        self.assertEqual(roll.status, status_number('loaded'))
