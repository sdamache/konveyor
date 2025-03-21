from django.test import TestCase
from konveyor.apps.api.serializers import ExampleModelSerializer
from konveyor.apps.users.serializers import UserSerializer

class ExampleModelSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {'name': 'Test Model', 'description': 'Test Description'}
        self.invalid_data = {'name': '', 'description': 'Test Description'}

    def test_example_model_serializer_valid(self):
        # Must have
        serializer = ExampleModelSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_example_model_serializer_invalid(self):
        # Must have
        serializer = ExampleModelSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())

class UserSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {'username': 'testuser', 'password': 'testpassword'}
        self.invalid_data = {'username': '', 'password': 'testpassword'}

    def test_user_serializer_valid(self):
        # Must have
        serializer = UserSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_user_serializer_invalid(self):
        # Must have
        serializer = UserSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
