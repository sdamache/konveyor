from django.test import TestCase
from konveyor.apps.core.validators import CoreValidator
from konveyor.apps.users.validators import UserValidator
from konveyor.apps.api.validators import APIValidator

class CoreValidatorTest(TestCase):
    def setUp(self):
        self.validator = CoreValidator()

    def test_core_validator_valid(self):
        # Must have
        self.assertTrue(self.validator.is_valid('valid_value'))

    def test_core_validator_invalid(self):
        # Must have
        self.assertFalse(self.validator.is_valid('invalid_value'))

class UserValidatorTest(TestCase):
    def setUp(self):
        self.validator = UserValidator()

    def test_user_validator_valid(self):
        # Must have
        self.assertTrue(self.validator.is_valid('valid_value'))

    def test_user_validator_invalid(self):
        # Must have
        self.assertFalse(self.validator.is_valid('invalid_value'))

class APIValidatorTest(TestCase):
    def setUp(self):
        self.validator = APIValidator()

    def test_api_validator_valid(self):
        # Must have
        self.assertTrue(self.validator.is_valid('valid_value'))

    def test_api_validator_invalid(self):
        # Must have
        self.assertFalse(self.validator.is_valid('invalid_value'))
