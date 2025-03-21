from django.test import TestCase
from rest_framework.metadata import SimpleMetadata
from konveyor.apps.api.models import ExampleModel
from konveyor.apps.api.serializers import ExampleModelSerializer

class SimpleMetadataTest(TestCase):
    def setUp(self):
        self.metadata = SimpleMetadata()
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.serializer = ExampleModelSerializer(instance=self.example_model)

    def test_get_serializer_info(self):
        # Must have
        serializer_info = self.metadata.get_serializer_info(self.serializer)
        self.assertIn('name', serializer_info)
        self.assertIn('description', serializer_info)
        self.assertEqual(serializer_info['name']['type'], 'string')
        self.assertEqual(serializer_info['description']['type'], 'string')
