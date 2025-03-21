from django.test import TestCase
from konveyor.apps.core.forms import CoreForm
from konveyor.apps.users.forms import UserForm
from konveyor.apps.api.forms import APIForm

class CoreFormTest(TestCase):
    def setUp(self):
        self.valid_data = {'name': 'Test Core'}
        self.invalid_data = {'name': ''}

    def test_core_form_valid(self):
        # Must have
        form = CoreForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_core_form_invalid(self):
        # Must have
        form = CoreForm(data=self.invalid_data)
        self.assertFalse(form.is_valid())

class UserFormTest(TestCase):
    def setUp(self):
        self.valid_data = {'username': 'testuser', 'password': 'testpassword'}
        self.invalid_data = {'username': '', 'password': 'testpassword'}

    def test_user_form_valid(self):
        # Must have
        form = UserForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_user_form_invalid(self):
        # Must have
        form = UserForm(data=self.invalid_data)
        self.assertFalse(form.is_valid())

class APIFormTest(TestCase):
    def setUp(self):
        self.valid_data = {'name': 'Test API'}
        self.invalid_data = {'name': ''}

    def test_api_form_valid(self):
        # Must have
        form = APIForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_api_form_invalid(self):
        # Must have
        form = APIForm(data=self.invalid_data)
        self.assertFalse(form.is_valid())
