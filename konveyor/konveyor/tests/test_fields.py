from django.test import TestCase
from konveyor.apps.core.fields import CoreField
from konveyor.apps.users.fields import UserField
from konveyor.apps.api.fields import APIField

class CoreFieldTest(TestCase):
    def setUp(self):
        self.field = CoreField()

    def test_core_field_initial(self):
        # Must have
        self.assertEqual(self.field.initial, None)

    def test_core_field_required(self):
        # Must have
        self.assertTrue(self.field.required)

class UserFieldTest(TestCase):
    def setUp(self):
        self.field = UserField()

    def test_user_field_initial(self):
        # Must have
        self.assertEqual(self.field.initial, None)

    def test_user_field_required(self):
        # Must have
        self.assertTrue(self.field.required)

class APIFieldTest(TestCase):
    def setUp(self):
        self.field = APIField()

    def test_api_field_initial(self):
        # Must have
        self.assertEqual(self.field.initial, None)

    def test_api_field_required(self):
        # Must have
        self.assertTrue(self.field.required)
