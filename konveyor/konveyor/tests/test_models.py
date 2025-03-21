from django.test import TestCase
from konveyor.apps.core.models import CoreModel
from konveyor.apps.users.models import User
from konveyor.apps.api.models import APIModel

class CoreModelTest(TestCase):
    def setUp(self):
        self.core_model = CoreModel.objects.create(name="Test Core Model")

    def test_core_model_creation(self):
        # Must have
        self.assertEqual(self.core_model.name, "Test Core Model")

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_user_creation(self):
        # Must have
        self.assertEqual(self.user.username, "testuser")

class APIModelTest(TestCase):
    def setUp(self):
        self.api_model = APIModel.objects.create(name="Test API Model")

    def test_api_model_creation(self):
        # Must have
        self.assertEqual(self.api_model.name, "Test API Model")
