from django.test import TestCase
from rest_framework.parsers import JSONParser
from konveyor.apps.api.models import ExampleModel
from konveyor.apps.api.serializers import ExampleModelSerializer
from io import BytesIO

class JSONParserTestCase(TestCase):
    def setUp(self):
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.serializer = ExampleModelSerializer(self.example_model)
        self.json_data = JSONParser().parse(BytesIO(self.serializer.data))

    def test_json_parser(self):
        # Must have
        self.assertEqual(self.json_data['name'], 'Test Model')
        self.assertEqual(self.json_data['description'], 'Test Description')
