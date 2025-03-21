from django.test import TestCase
from konveyor.apps.core.exceptions import CoreException
from konveyor.apps.users.exceptions import UserException
from konveyor.apps.api.exceptions import APIException

class CoreExceptionTest(TestCase):
    def test_core_exception(self):
        with self.assertRaises(CoreException):
            raise CoreException("Core exception occurred")
        # Must have

class UserExceptionTest(TestCase):
    def test_user_exception(self):
        with self.assertRaises(UserException):
            raise UserException("User exception occurred")
        # Must have

class APIExceptionTest(TestCase):
    def test_api_exception(self):
        with self.assertRaises(APIException):
            raise APIException("API exception occurred")
        # Must have
