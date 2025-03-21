from django.test import TestCase
from konveyor.apps.core.models import CoreModel
from konveyor.apps.users.models import User
from konveyor.apps.api.models import APIModel

class CoreModelQuerySetTest(TestCase):
    def setUp(self):
        self.core_model = CoreModel.objects.create(name="Test Core Model")

    def test_core_model_queryset(self):
        # Must have
        queryset = CoreModel.objects.filter(name="Test Core Model")
        self.assertEqual(queryset.count(), 1)

class UserQuerySetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_user_queryset(self):
        # Must have
        queryset = User.objects.filter(username="testuser")
        self.assertEqual(queryset.count(), 1)

class APIModelQuerySetTest(TestCase):
    def setUp(self):
        self.api_model = APIModel.objects.create(name="Test API Model")

    def test_api_model_queryset(self):
        # Must have
        queryset = APIModel.objects.filter(name="Test API Model")
        self.assertEqual(queryset.count(), 1)
