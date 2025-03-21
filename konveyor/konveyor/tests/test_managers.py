from django.test import TestCase
from konveyor.apps.core.managers import CoreManager
from konveyor.apps.users.managers import UserManager
from konveyor.apps.api.managers import APIManager

class CoreManagerTest(TestCase):
    def setUp(self):
        self.manager = CoreManager()

    def test_core_manager_process(self):
        # Must have
        result = self.manager.process(data="Test Data")
        self.assertEqual(result, "Processed: Test Data")

class UserManagerTest(TestCase):
    def setUp(self):
        self.manager = UserManager()

    def test_user_manager_process(self):
        # Must have
        result = self.manager.process(data="Test User Data")
        self.assertEqual(result, "Processed: Test User Data")

class APIManagerTest(TestCase):
    def setUp(self):
        self.manager = APIManager()

    def test_api_manager_process(self):
        # Must have
        result = self.manager.process(data="Test API Data")
        self.assertEqual(result, "Processed: Test API Data")
