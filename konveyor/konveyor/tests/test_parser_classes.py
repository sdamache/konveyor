from django.test import TestCase
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
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

class FormParserTestCase(TestCase):
    def setUp(self):
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.serializer = ExampleModelSerializer(self.example_model)
        self.form_data = FormParser().parse(BytesIO(self.serializer.data))

    def test_form_parser(self):
        # Good to have
        self.assertEqual(self.form_data['name'], 'Test Model')
        self.assertEqual(self.form_data['description'], 'Test Description')

class MultiPartParserTestCase(TestCase):
    def setUp(self):
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.serializer = ExampleModelSerializer(self.example_model)
        self.multipart_data = MultiPartParser().parse(BytesIO(self.serializer.data))

    def test_multipart_parser(self):
        # Future enhancement
        self.assertEqual(self.multipart_data['name'], 'Test Model')
        self.assertEqual(self.multipart_data['description'], 'Test Description')
