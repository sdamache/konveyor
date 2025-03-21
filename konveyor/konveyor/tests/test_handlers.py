from django.test import TestCase
from konveyor.apps.core.handlers import CoreHandler
from konveyor.apps.users.handlers import UserHandler
from konveyor.apps.api.handlers import APIHandler

class CoreHandlerTest(TestCase):
    def setUp(self):
        self.handler = CoreHandler()

    def test_core_handler_process(self):
        # Must have
        result = self.handler.process(data="Test Data")
        self.assertEqual(result, "Processed: Test Data")

class UserHandlerTest(TestCase):
    def setUp(self):
        self.handler = UserHandler()

    def test_user_handler_process(self):
        # Must have
        result = self.handler.process(data="Test User Data")
        self.assertEqual(result, "Processed: Test User Data")

class APIHandlerTest(TestCase):
    def setUp(self):
        self.handler = APIHandler()

    def test_api_handler_process(self):
        # Must have
        result = self.handler.process(data="Test API Data")
        self.assertEqual(result, "Processed: Test API Data")
